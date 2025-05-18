import nltk
import pandas as pd
import os
from transformers import AutoTokenizer, TFAutoModelForSequenceClassification, pipeline
from nltk.tokenize import sent_tokenize

class BiasDetector:
    def __init__(self):
        # Define o diretório de cache para os modelos
        cache_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "models")
        os.makedirs(cache_dir, exist_ok=True)
        
        # Certifique-se de que os recursos NLTK estão baixados
        try:
            nltk.data.find('tokenizers/punkt')
        except LookupError:
            nltk.download('punkt', download_dir=cache_dir)
            nltk.data.path.append(cache_dir)
            
        # Carrega o modelo pré-treinado com cache local
        self.model_name = "cffl/bert-base-styleclassification-subjective-neutral"
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name, cache_dir=cache_dir)
        self.model = TFAutoModelForSequenceClassification.from_pretrained(
            self.model_name, 
            from_pt=True, 
            cache_dir=cache_dir
        )
        
        # Inicializa o pipeline de classificação
        self.classifier = pipeline(
            "text-classification",
            model=self.model,
            tokenizer=self.tokenizer,
            framework="tf",
            top_k=None
        )
        
    def split_text_to_df(self, text):
        """Divide o texto em sentenças e cria um DataFrame"""
        sentences = sent_tokenize(text, language='english')
        return pd.DataFrame({'sentence': sentences})
        
    def detect_bias(self, df):
        """Detecta viés em cada sentença do DataFrame"""
        labels = []
        bias_scores = []
        
        for sent in df['sentence']:
            try:
                scores = self.classifier(sent, top_k=None)  # [{'label':..., 'score':...}, ...]
                best = max(scores, key=lambda x: x['score'])  # escolhe a classe de maior confiança
                labels.append(best['label'])  # label idêntico ao retornado
                bias_scores.append(best['score'])  # score dessa classe
            except Exception as e:
                # Se ocorrer algum erro, marca como "ERROR" com score 0
                labels.append("ERROR")
                bias_scores.append(0.0)
                
        df['label'] = labels
        df['bias_score'] = bias_scores
        return df
        
    def analyze_text(self, text):
        """Analisa um texto completo e retorna o DataFrame com as análises"""
        df = self.split_text_to_df(text)
        return self.detect_bias(df)
    
    def get_summary(self, df):
        """Retorna um resumo da análise de viés do texto"""
        if 'label' not in df.columns:
            return {"error": "Texto não analisado corretamente"}
            
        total = len(df)
        subjective = len(df[df['label'] == 'SUBJECTIVE'])
        neutral = len(df[df['label'] == 'NEUTRAL'])
        
        # Calculando porcentagens
        perc_subjective = (subjective / total) * 100 if total > 0 else 0
        perc_neutral = (neutral / total) * 100 if total > 0 else 0
        
        # Calculando score médio de viés
        avg_bias = df['bias_score'].mean() if 'bias_score' in df.columns else 0
        
        # Determinando o nível geral de viés
        if perc_subjective >= 70:
            bias_level = "Alto"
        elif perc_subjective >= 40:
            bias_level = "Médio"
        else:
            bias_level = "Baixo"
            
        return {
            "total_sentences": total,
            "subjective_sentences": subjective,
            "neutral_sentences": neutral,
            "perc_subjective": perc_subjective,
            "perc_neutral": perc_neutral,
            "avg_bias_score": avg_bias,
            "bias_level": bias_level
        } 