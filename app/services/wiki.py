"""
Serviço para acesso à API da Wikipedia e estatísticas de visualização
"""
import asyncio
import aiohttp
import requests
import pandas as pd
from datetime import datetime, timedelta

class WikiService:
    # Constantes da API
    WIKI_API = "https://en.wikipedia.org/w/api.php"
    PAGEVIEWS_PER_ARTICLE = "https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article"
    PROJECT = "en.wikipedia"
    ACCESS = "all-access"
    AGENT = "user"
    GRANULARITY = "daily"
    
    def __init__(self):
        pass
        
    def search_titles(self, topic, limit=100):
        """Busca títulos relacionados a um tópico específico"""
        print(f"Buscando títulos para o tópico: '{topic}', limite: {limit}")
        params = {
            "action":  "query",
            "format":  "json",
            "list":    "search",
            "srsearch": topic,
            "srlimit": limit,
            "srsort":  "relevance",
            "srprop":  ""
        }
        try:
            r = requests.get(self.WIKI_API, params=params)
            r.raise_for_status()  # Verificar se a requisição foi bem-sucedida
            response_data = r.json()
            titles = [i["title"] for i in response_data.get("query", {}).get("search", [])]
            print(f"Encontrados {len(titles)} artigos para o tópico '{topic}'")
            return titles
        except Exception as e:
            print(f"ERRO ao buscar títulos para '{topic}': {e}")
            return []

    def get_relevant_titles(self, topics, target_count=20):
        """Obtém títulos relevantes para uma lista de tópicos"""
        print(f"Buscando títulos relevantes para tópicos: {topics}, alvo: {target_count}")
        if not topics:
            print("AVISO: Lista de tópicos vazia!")
            return []
            
        titles = []
        titles_per_topic = max(5, target_count // len(topics))  # Distribuir equitativamente
        print(f"Buscando até {titles_per_topic} títulos por tópico")
        
        for t in topics:
            for title in self.search_titles(t, limit=titles_per_topic * 2):  # Buscar o dobro para ter margem
                if title not in titles:
                    titles.append(title)
                if len(titles) >= target_count * 2:  # Ter o dobro para filtrar com views
                    break
            
            if len(titles) >= target_count * 2:
                break
        
        print(f"Total de títulos únicos encontrados: {len(titles)}")        
        return titles
    
    async def fetch_views(self, session, title, date_dt):
        """Busca contagem de visualizações para um artigo específico"""
        date_str = date_dt.strftime("%Y%m%d")
        url = f"{self.PAGEVIEWS_PER_ARTICLE}/{self.PROJECT}/{self.ACCESS}/{self.AGENT}/{title.replace(' ', '_')}/{self.GRANULARITY}/{date_str}/{date_str}"
        try:
            async with session.get(url, timeout=10) as resp:
                if resp.status != 200:
                    print(f"AVISO: Status {resp.status} ao buscar views para '{title}'")
                    # Em caso de erro, retornar None ao invés de um valor padrão
                    return title, None
                data = await resp.json()
            views = data.get("items", [{}])[0].get("views", 0)
            return title, views
        except Exception as e:
            print(f"ERRO ao buscar views para '{title}': {e}")
            # Em caso de exceção, retornar None
            return title, None
            
    async def fetch_page(self, session, title, views):
        """Busca detalhes completos de uma página da Wikipedia"""
        params = {
            "action":      "query",
            "format":      "json",
            "prop":        "extracts|info|pageimages",
            "explaintext": 1,
            "redirects":   1,
            "inprop":      "url",
            "piprop":      "original",
            "titles":      title
        }
        try:
            async with session.get(self.WIKI_API, params=params) as resp:
                js = await resp.json()
            page = next(iter(js.get("query", {}).get("pages", {}).values()), {})
            pid = page.get("pageid")
            if not pid or "missing" in page:
                return None
            text = page.get("extract", "")
            summary = text.split("\n\n")[0] if text else ""
            article_data = {
                "id":      pid,
                "title":   page.get("title", ""),
                "url":     page.get("fullurl", ""),
                "summary": summary,
                "content": text,
                "image":   page.get("original", {}).get("source")
            }
            # Só adiciona views se não for None
            if views is not None:
                article_data["views"] = views
            
            return article_data
        except Exception:
            return None
            
    async def get_trending_articles(self, topics, top_k=10, date_str=None):
        """Função principal para obter artigos relevantes e populares"""
        print(f"\n=== Iniciando busca de artigos ===")
        print(f"Tópicos: {topics}")
        print(f"Quantidade desejada: {top_k}")
        
        # Define data alvo
        if date_str:
            try:
                date_dt = datetime.strptime(date_str, "%Y/%m/%d").date()
                print(f"Data específica: {date_dt}")
            except ValueError:
                date_dt = datetime.utcnow().date() - timedelta(days=1)
                print(f"Data específica inválida, usando ontem: {date_dt}")
        else:
            date_dt = datetime.utcnow().date() - timedelta(days=1)
            print(f"Usando data padrão (ontem): {date_dt}")
            
        # Busca títulos relevantes (buscamos o dobro para depois filtrar por views)
        print("Buscando títulos relevantes...")
        relevant_titles = self.get_relevant_titles(topics, target_count=top_k)
        print(f"Total de títulos encontrados: {len(relevant_titles)}")
        
        if not relevant_titles:
            print("ERRO: Nenhum título relevante encontrado!")
            return pd.DataFrame(columns=["id", "title", "url", "summary", "content", "image", "views", "score", "topics"])
        
        # Busca views
        print("Buscando dados de visualização...")
        async with aiohttp.ClientSession() as session:
            vs_tasks = [self.fetch_views(session, t, date_dt) for t in relevant_titles]
            vs_results = await asyncio.gather(*vs_tasks)

        # Trata artigos com/sem visualizações
        vs_dict = dict(vs_results)
        
        # Prioriza artigos com visualizações
        titles_with_views = [(t, v) for t, v in vs_results if v is not None and v > 0]
        print(f"Artigos com visualizações > 0: {len(titles_with_views)}")
        
        if titles_with_views:
            # Tem artigos com visualizações, ordena por número de views
            titles_with_views.sort(key=lambda x: x[1], reverse=True)
            top_titles = [t for t, _ in titles_with_views[:top_k]]
        else:
            print("AVISO: Nenhum artigo com visualizações encontrado!")
            # Usa todos os títulos sem filtrar/ordenar por visualizações
            top_titles = relevant_titles[:top_k]
        
        print(f"Top títulos selecionados: {len(top_titles)}")

        # Busca detalhes
        print("Buscando detalhes completos dos artigos...")
        async with aiohttp.ClientSession() as session:
            pg_tasks = [self.fetch_page(session, t, vs_dict.get(t)) for t in top_titles]
            pages = await asyncio.gather(*pg_tasks)

        # Monta DataFrame
        articles = [p for p in pages if p]
        print(f"Artigos recuperados com sucesso: {len(articles)}")
        
        if not articles:
            print("ERRO: Não foi possível recuperar os detalhes de nenhum artigo!")
            return pd.DataFrame(columns=["id", "title", "url", "summary", "content", "image", "views", "score", "topics"])
        
        # Calcula score de tópicos
        topic_keywords = [kw.lower() for kw in topics]
        for art in articles:
            txt = " ".join([art["title"], art["summary"], art["content"]]).lower()
            art["score"] = sum(kw in txt for kw in topic_keywords)
            # Guardar os tópicos usados na busca para referência futura
            art["topics"] = topics

        df = pd.DataFrame(articles)
        if not df.empty:
            # Ordena por views (quando disponível) e score
            if "views" in df.columns:
                df = df.sort_values(["views", "score"], ascending=False).reset_index(drop=True)
            else:
                df = df.sort_values("score", ascending=False).reset_index(drop=True)
            print(f"=== Busca concluída com sucesso: {len(df)} artigos encontrados ===")
            return df
            
        print("ERRO: DataFrame vazio após todo o processamento!")
        return pd.DataFrame(columns=["id", "title", "url", "summary", "content", "image", "views", "score", "topics"])
        
    def get_articles(self, topics, k=20, date_str=None, **kwargs):
        """Método simplificado para buscar artigos"""
        print(f"get_articles chamado com tópicos: {topics}, k={k}, date_str={date_str}")
        if not topics:
            print("ERRO: Nenhum tópico fornecido!")
            return pd.DataFrame(columns=["id", "title", "url", "summary", "content", "image", "views", "score", "topics"])
            
        return asyncio.run(self.get_trending_articles(topics, top_k=k, date_str=date_str)) 