#!/usr/bin/env python3
"""Quick test script for MedCPT models."""

from polus.aithena.clinical_aithena.embeddings.medcpt_service import MedCPTService

def main():
    print("🧪 Testing MedCPT Models\n")
    
    # Initialize service
    print("Initializing MedCPTService...")
    service = MedCPTService()
    
    # Test article encoding
    title = "Phase 3 Trial of Pembrolizumab for Advanced Melanoma"
    text = "This randomized controlled trial evaluates pembrolizumab in patients with advanced melanoma and BRAF mutation. Primary endpoint is overall survival."
    print(f"\n📄 Testing article encoding:")
    print(f"   Title: '{title}'")
    print(f"   Text: '{text[:50]}...'")
    article_embedding = service.encode_article(title, text)
    print(f"   ✅ Embedding shape: {len(article_embedding)} dimensions")
    print(f"   First 5 values: {[f'{v:.4f}' for v in article_embedding[:5]]}")
    
    # Test query encoding
    query = "melanoma immunotherapy clinical trials"
    print(f"\n🔍 Testing query encoding:")
    print(f"   Text: '{query}'")
    query_embedding = service.encode_query(query)
    print(f"   ✅ Embedding shape: {len(query_embedding)} dimensions")
    print(f"   First 5 values: {[f'{v:.4f}' for v in query_embedding[:5]]}")
    
    # Test batch encoding
    articles = [
        ("Nivolumab for NSCLC", "Randomized trial of nivolumab in non-small cell lung cancer patients"),
        ("Atezolizumab for TNBC", "Study of atezolizumab in triple-negative breast cancer"),
        ("Durvalumab for Bladder Cancer", "Clinical trial of durvalumab for advanced bladder cancer")
    ]
    print(f"\n📚 Testing batch article encoding ({len(articles)} articles):")
    batch_embeddings = service.encode_articles_batch(articles)
    print(f"   ✅ Generated {len(batch_embeddings)} embeddings")
    print(f"   Each embedding: {len(batch_embeddings[0])} dimensions")
    
    # Test batch query encoding
    queries = [
        "lung cancer immunotherapy",
        "breast cancer treatment",
        "bladder cancer clinical trials"
    ]
    print(f"\n🔍 Testing batch query encoding ({len(queries)} queries):")
    query_embeddings = service.encode_queries_batch(queries)
    print(f"   ✅ Generated {len(query_embeddings)} embeddings")
    print(f"   Each embedding: {len(query_embeddings[0])} dimensions")
    
    print("\n✅ All MedCPT tests passed!")
    print(f"\n📊 Summary:")
    print(f"   - Article encoder: medcpt-article")
    print(f"   - Query encoder: medcpt-query")
    print(f"   - Embedding dimensions: {len(article_embedding)}")
    print(f"   - Models accessible via LiteLLM proxy")

if __name__ == "__main__":
    main()
