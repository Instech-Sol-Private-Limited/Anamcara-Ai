import fitz
import chromadb
from sentence_transformers import SentenceTransformer
import os

def extract_text(path):
    """Extract text from PDF"""
    try:
        doc = fitz.open(path)
        text = ""
        for page in doc:
            text += page.get_text("text") + "\n"
        doc.close()
        return text
    except Exception as e:
        print(f" Error extracting text from {path}: {e}")
        return ""

def chunk_text(text, chunk_size=400):
    """Split text into chunks"""
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size):
        chunk = " ".join(words[i:i+chunk_size])
        if chunk.strip():  # Only add non-empty chunks
            chunks.append(chunk)
    return chunks

# ------ MAIN BUILD PROCESS ------
if __name__ == "__main__":
    print(" Starting embedding build process...\n")
    
    # Initialize embedder
    print(" Loading SentenceTransformer model...")
    embedder = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    print(" Model loaded!\n")

    # Get absolute paths
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    pdf_paths = [
        os.path.join(base_dir, "pdfs", "Admin_Master_URD.pdf"),
        os.path.join(base_dir, "pdfs", "User_Master_URD.pdf"),
        os.path.join(base_dir, "pdfs", "Desire_Core_Prompts.pdf"),
    ]

    # Verify PDFs exist
    print(" Checking PDF files...")
    for pdf in pdf_paths:
        if os.path.exists(pdf):
            print(f"    Found: {os.path.basename(pdf)}")
        else:
            print(f"    Missing: {pdf}")
            print(f"      Please ensure this file exists!")
    print()

    # Setup ChromaDB
    chroma_path = os.path.join(base_dir, "chroma_db")
    os.makedirs(chroma_path, exist_ok=True)
    print(f" ChromaDB path: {chroma_path}\n")
    
    client = chromadb.PersistentClient(path=chroma_path)
    
    # Delete existing collection if it exists (fresh start)
    try:
        client.delete_collection("anamcore_pdf")
        print("  Deleted existing collection\n")
    except:
        pass
    
    # Create new collection
    collection = client.create_collection("anamcore_pdf")
    print(" Created new collection: anamcore_pdf\n")

    total_chunks = 0
    
    # Process each PDF
    for pdf in pdf_paths:
        if not os.path.exists(pdf):
            print(f"  Skipping missing file: {pdf}\n")
            continue
            
        print(f" Processing: {os.path.basename(pdf)}")
        
        # Extract text
        text = extract_text(pdf)
        if not text:
            print(f"     No text extracted, skipping\n")
            continue
        
        print(f"    Extracted {len(text)} characters")
        
        # Chunk text
        chunks = chunk_text(text, chunk_size=400)
        print(f"     Created {len(chunks)} chunks")
        
        # Add to ChromaDB
        print(f"    Adding to database...")
        for idx, chunk in enumerate(chunks):
            try:
                embedding = embedder.encode(chunk).tolist()
                doc_id = f"{os.path.basename(pdf)}_{idx}"
                
                collection.add(
                    documents=[chunk],
                    embeddings=[embedding],
                    ids=[doc_id]
                )
                
                # Progress indicator every 50 chunks
                if (idx + 1) % 50 == 0:
                    print(f"      Added {idx + 1}/{len(chunks)} chunks...")
                    
            except Exception as e:
                print(f"    Error adding chunk {idx}: {e}")
                continue
        
        total_chunks += len(chunks)
        print(f"    Done! Added {len(chunks)} chunks\n")

    # Verify collection
    print("="*60)
    count = collection.count()
    print(f" Embedding build complete!")
    print(f" Total documents in collection: {count}")
    print(f" Stored in: {chroma_path}")
    
    if count == 0:
        print("\n  WARNING: No documents were added!")
        print("   Check that your PDF files contain extractable text")
    else:
        # Test retrieval
        print("\n Testing retrieval...")
        test_results = collection.query(
            query_texts=["What is Anamcara?"],
            n_results=1
        )
        if test_results['documents'][0]:
            print(f" Retrieval works! Sample result:")
            print(f"   {test_results['documents'][0][0][:150]}...")
    
    print("\n" + "="*60)
    print(" Done! You can now start your FastAPI server.")