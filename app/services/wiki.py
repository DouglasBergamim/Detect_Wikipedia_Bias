import asyncio
import aiohttp
import requests
import pandas as pd
from urllib.parse import quote
from datetime import datetime, timedelta

class WikiService:
    WIKI_API = "https://en.wikipedia.org/w/api.php"
    PAGEVIEWS_PER_ARTICLE = "https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article"
    PROJECT = "en.wikipedia"
    ACCESS = "all-access"
    AGENT = "user"
    GRANULARITY = "daily"
    
    def __init__(self):
        pass
        
    def search_titles(self, topic, limit=100):
        """Search for titles related to a specific topic"""
        print(f"Searching titles for topic: '{topic}', limit: {limit}")
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
            r.raise_for_status()  # Check if request was successful
            response_data = r.json()
            titles = [i["title"] for i in response_data.get("query", {}).get("search", [])]
            print(f"Found {len(titles)} articles for topic '{topic}'")
            return titles
        except Exception as e:
            print(f"ERROR searching titles for '{topic}': {e}")
            return []

    def get_relevant_titles(self, topics, target_count=20):
        """Get relevant titles for a list of topics"""
        print(f"Searching relevant titles for topics: {topics}, target: {target_count}")
        if not topics:
            print("WARNING: Empty topics list!")
            return []
            
        titles = []
        titles_per_topic = max(5, target_count // len(topics))  # Distribute evenly
        print(f"Searching up to {titles_per_topic} titles per topic")
        
        for t in topics:
            for title in self.search_titles(t, limit=titles_per_topic * 2):  # Search double to have margin
                if title not in titles:
                    titles.append(title)
                if len(titles) >= target_count * 2:  # Have double to filter by views
                    break
            
            if len(titles) >= target_count * 2:
                break
        
        print(f"Total unique titles found: {len(titles)}")        
        return titles
    
    async def fetch_views(self, session, title, date_dt):
        """Fetch view count for a specific article"""
        date_str = date_dt.strftime("%Y%m%d")
        url = f"{self.PAGEVIEWS_PER_ARTICLE}/{self.PROJECT}/{self.ACCESS}/{self.AGENT}/{quote(title, safe='')}/{self.GRANULARITY}/{date_str}/{date_str}"
        try:
            async with session.get(url, timeout=10) as resp:
                if resp.status != 200:
                    print(f"WARNING: Status {resp.status} when fetching views for '{title}'")
                    # In case of error, return 10 views (default value) to allow article to continue in process
                    return title, 10
                data = await resp.json()
            views = data.get("items", [{}])[0].get("views", 0)
            return title, views
        except Exception as e:
            print(f"ERROR fetching views for '{title}': {e}")
            # In case of exception, return 10 views for this article
            return title, 10       
   
    async def fetch_page(self, session, title, views):
        """Fetch complete details of a Wikipedia page"""
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
            
    async def get_trending_articles(self, topics, top_k=10, date_str=None):
        """Main function to get relevant and popular articles"""
        print(f"\n=== Starting article search ===")
        print(f"Topics: {topics}")
        print(f"Desired quantity: {top_k}")
        
        # Define target date
        if date_str:
            try:
                date_dt = datetime.strptime(date_str, "%Y/%m/%d").date()
                print(f"Specific date: {date_dt}")
            except ValueError:
                date_dt = datetime.utcnow().date() - timedelta(days=1)
                print(f"Invalid specific date, using yesterday: {date_dt}")
        else:
            date_dt = datetime.utcnow().date() - timedelta(days=1)
            print(f"Using default date (yesterday): {date_dt}")
            
        # Search relevant titles (we search double to filter by views later)
        print("Searching relevant titles...")
        relevant_titles = self.get_relevant_titles(topics, target_count=top_k)
        print(f"Total titles found: {len(relevant_titles)}")
        
        if not relevant_titles:
            print("ERROR: No relevant titles found!")
            return pd.DataFrame(columns=["id", "title", "url", "summary", "content", "image", "views", "score", "topics"])
        
        # Fetch views
        print("Fetching view data...")
        async with aiohttp.ClientSession() as session:
            vs_tasks = [self.fetch_views(session, t, date_dt) for t in relevant_titles]
            vs_results = await asyncio.gather(*vs_tasks)

        # Filter only those with views > 0 and sort
        vs_filtered = [(t, v) for t, v in vs_results if v > 0]
        print(f"Articles with views > 0: {len(vs_filtered)}")
        
        if not vs_filtered:
            print("WARNING: No articles with views found!")
            # Use all titles without filtering by views
            vs_filtered = [(t, 1) for t in relevant_titles[:top_k]]
            print(f"Using {len(vs_filtered)} articles without view data")
            
        vs_filtered.sort(key=lambda x: x[1], reverse=True)
        top_titles = [t for t, _ in vs_filtered[:top_k]]
        print(f"Top titles selected: {len(top_titles)}")

        # Fetch details
        print("Fetching complete article details...")
        async with aiohttp.ClientSession() as session:
            pg_tasks = [self.fetch_page(session, t, dict(vs_results).get(t, 1)) for t in top_titles]
            pages = await asyncio.gather(*pg_tasks)

        # Build DataFrame
        articles = [p for p in pages if p]
        print(f"Articles successfully retrieved: {len(articles)}")
        
        if not articles:
            print("ERROR: Could not retrieve details for any article!")
            return pd.DataFrame(columns=["id", "title", "url", "summary", "content", "image", "views", "score", "topics"])
        
        # Calculate topic score
        topic_keywords = [kw.lower() for kw in topics]
        for art in articles:
            txt = " ".join([art["title"], art["summary"], art["content"]]).lower()
            art["score"] = sum(kw in txt for kw in topic_keywords)
            # Store topics used in search for future reference
            art["topics"] = topics

        df = pd.DataFrame(articles)
        if not df.empty:
            df = df.sort_values(["views","score"], ascending=False).reset_index(drop=True)
            print(f"=== Search completed successfully: {len(df)} articles found ===")
            return df
            
        print("ERROR: Empty DataFrame after all processing!")
        return pd.DataFrame(columns=["id", "title", "url", "summary", "content", "image", "views", "score", "topics"])
        
    def get_articles(self, topics, k=20, date_str=None, **kwargs):
        """Simplified method to search articles"""
        """Método simplificado para buscar artigos"""
        print(f"get_articles chamado com tópicos: {topics}, k={k}, date_str={date_str}")
        if not topics:
            print("ERRO: Nenhum tópico fornecido!")
            return pd.DataFrame(columns=["id", "title", "url", "summary", "content", "image", "views", "score", "topics"])
            
        return asyncio.run(self.get_trending_articles(topics, top_k=k, date_str=date_str)) 