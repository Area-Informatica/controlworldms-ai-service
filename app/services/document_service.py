import io
from pypdf import PdfReader
from fastapi import UploadFile

async def extract_text_from_file(file: UploadFile) -> str:
    """
    Extrae texto plano de un archivo PDF o TXT.
    Para imágenes o PDFs escaneados requeriría OCR (tesseract), 
    pero por ahora nos limitamos a texto seleccionable para ahorrar recursos.
    """
    content = await file.read()
    
    if file.filename.lower().endswith('.pdf'):
        try:
            reader = PdfReader(io.BytesIO(content))
            text = ""
            # Limite de seguridad: solo primeras 5 paginas para evitar consumo excesivo
            max_pages = min(len(reader.pages), 5)
            for i in range(max_pages):
                page_text = reader.pages[i].extract_text()
                if page_text:
                    text += page_text + "\n"
            return text
        except Exception as e:
            return f"Error leyendo PDF: {str(e)}"
            
    elif file.filename.lower().endswith('.txt'):
        return content.decode('utf-8')
        
    else:
        return "Formato no soportado. Por favor sube archivos PDF o TXT."
