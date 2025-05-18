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
        params = {
            "action":  "query",
            "format":  "json",
            "list":    "search",
            "srsearch": topic,
            "srlimit": limit,
            "srsort":  "relevance",
            "srprop":  ""
        }
        r = requests.get(self.WIKI_API, params=params)
        return [i["title"] for i in r.json().get("query", {}).get("search", [])]

    def get_relevant_titles(self, topics, max_candidates=500):
        """Obtém títulos relevantes para uma lista de tópicos"""
        titles = []
        for t in topics:
            for title in self.search_titles(t):
                if title not in titles:
                    titles.append(title)
                if len(titles) >= max_candidates:
                    return titles
        return titles
    
    async def fetch_views(self, session, title, date_dt):
        """Busca contagem de visualizações para um artigo específico"""
        date_str = date_dt.strftime("%Y%m%d")
        url = f"{self.PAGEVIEWS_PER_ARTICLE}/{self.PROJECT}/{self.ACCESS}/{self.AGENT}/{title.replace(' ', '_')}/{self.GRANULARITY}/{date_str}/{date_str}"
        try:
            async with session.get(url) as resp:
                if resp.status != 200:
                    return title, 0
                data = await resp.json()
            views = data.get("items", [{}])[0].get("views", 0)
            return title, views
        except Exception:
            return title, 0
            
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
            return {
                "id":      pid,
                "title":   page.get("title", ""),
                "url":     page.get("fullurl", ""),
                "summary": summary,
                "content": text,
                "image":   page.get("original", {}).get("source"),
                "views":   views
            }
        except Exception:
            return None
            
    async def get_trending_articles(self, topics, max_candidates=500, top_k=10, date_str=None):
        """Função principal para obter artigos relevantes e populares"""
        # Define data alvo
        if date_str:
            try:
                date_dt = datetime.strptime(date_str, "%Y/%m/%d").date()
            except ValueError:
                date_dt = datetime.utcnow().date() - timedelta(days=1)
        else:
            date_dt = datetime.utcnow().date() - timedelta(days=1)
            
        # Busca títulos relevantes
        relevant_titles = self.get_relevant_titles(topics, max_candidates)
        
        # Busca views
        async with aiohttp.ClientSession() as session:
            vs_tasks = [self.fetch_views(session, t, date_dt) for t in relevant_titles]
            vs_results = await asyncio.gather(*vs_tasks)

        # Filtra só quem teve views > 0 e ordena
        vs_filtered = [(t, v) for t, v in vs_results if v > 0]
        vs_filtered.sort(key=lambda x: x[1], reverse=True)
        top_titles = [t for t, _ in vs_filtered[:top_k]]

        # Busca detalhes
        async with aiohttp.ClientSession() as session:
            pg_tasks = [self.fetch_page(session, t, dict(vs_results)[t]) for t in top_titles]
            pages = await asyncio.gather(*pg_tasks)

        # Monta DataFrame
        articles = [p for p in pages if p]
        
        # Calcula score de tópicos
        topic_keywords = [kw.lower() for kw in topics]
        for art in articles:
            txt = " ".join([art["title"], art["summary"], art["content"]]).lower()
            art["score"] = sum(kw in txt for kw in topic_keywords)

        df = pd.DataFrame(articles)
        if not df.empty:
            return df.sort_values(["views","score"], ascending=False).reset_index(drop=True)
        return pd.DataFrame(columns=["id", "title", "url", "summary", "content", "image", "views", "score"]) 