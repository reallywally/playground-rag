import re
import fitz  # PyMuPDF
from typing import List, Dict, Any, Optional, Tuple
from langchain.schema import Document
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
try:
    from config.settings import settings
except ImportError:
    # Fallback settings for development
    class Settings:
        EMBEDDING_MODEL = "text-embedding-3-large"
        OPENAI_API_KEY = ""
        USE_SEMANTIC_CHUNKING = True
        SEMANTIC_CHUNK_MIN_SIZE = 100
        SEMANTIC_CHUNK_MAX_SIZE = 1500
        SENTENCE_SIMILARITY_THRESHOLD = 0.7
        REMOVE_HEADERS_FOOTERS = True
        EXTRACT_TABLES = True
        EXTRACT_IMAGES = True
        MIN_TEXT_LENGTH = 50
        CHUNK_SIZE = 1000
        CHUNK_OVERLAP = 200
    settings = Settings()


class EnhancedDocumentProcessor:
    """향상된 문서 처리 클래스 - semantic chunking 및 메타데이터 강화"""
    
    def __init__(self):
        try:
            self.embeddings = OpenAIEmbeddings(
                model=settings.EMBEDDING_MODEL,
                openai_api_key=settings.OPENAI_API_KEY
            )
        except Exception as e:
            print(f"Warning: OpenAI embeddings initialization failed: {e}")
            self.embeddings = None
    
    def process_pdf_enhanced(self, file_path: str, filename: str) -> List[Document]:
        """PDF를 향상된 방식으로 처리합니다."""
        try:
            # PDF 문서 열기
            pdf_document = fitz.open(file_path)
            documents = []
            
            for page_num in range(len(pdf_document)):
                page = pdf_document[page_num]
                
                # 페이지에서 다양한 정보 추출
                page_data = self._extract_page_content(page, page_num + 1, filename)
                
                # 텍스트가 있으면 문서로 변환
                if page_data['text'] and len(page_data['text'].strip()) >= settings.MIN_TEXT_LENGTH:
                    documents.extend(self._create_documents_from_page(page_data))
            
            pdf_document.close()
            
            # Semantic chunking 적용
            if settings.USE_SEMANTIC_CHUNKING and documents:
                documents = self._apply_semantic_chunking(documents)
            
            return documents
            
        except Exception as e:
            raise Exception(f"Enhanced PDF processing failed: {str(e)}")
    
    def _extract_page_content(self, page, page_num: int, filename: str) -> Dict[str, Any]:
        """페이지에서 텍스트, 테이블, 이미지 정보를 추출합니다."""
        page_data = {
            'text': '',
            'tables': [],
            'images': [],
            'headers': [],
            'footers': [],
            'page_num': page_num,
            'filename': filename
        }
        
        # 1. 기본 텍스트 추출
        raw_text = page.get_text()
        
        # 2. 구조화된 텍스트 추출 (블록 단위)
        blocks = page.get_text("dict")
        
        # 3. 헤더/푸터 감지 및 제거
        if settings.REMOVE_HEADERS_FOOTERS:
            cleaned_text, headers, footers = self._remove_headers_footers(raw_text, page)
            page_data['text'] = cleaned_text
            page_data['headers'] = headers
            page_data['footers'] = footers
        else:
            page_data['text'] = raw_text
        
        # 4. 테이블 추출
        if settings.EXTRACT_TABLES:
            page_data['tables'] = self._extract_tables(page)
        
        # 5. 이미지 정보 추출
        if settings.EXTRACT_IMAGES:
            page_data['images'] = self._extract_image_info(page)
        
        # 6. 제목 및 섹션 헤더 감지
        page_data['sections'] = self._extract_sections(blocks)
        
        return page_data
    
    def _remove_headers_footers(self, text: str, page) -> Tuple[str, List[str], List[str]]:
        """헤더와 푸터를 감지하고 제거합니다."""
        lines = text.split('\n')
        if len(lines) <= 3:
            return text, [], []
        
        headers = []
        footers = []
        content_lines = lines[:]
        
        # 상단 3줄에서 헤더 패턴 감지
        for i in range(min(3, len(lines))):
            line = lines[i].strip()
            if self._is_header_footer_pattern(line):
                headers.append(line)
                content_lines[i] = ''
        
        # 하단 3줄에서 푸터 패턴 감지
        for i in range(max(0, len(lines) - 3), len(lines)):
            line = lines[i].strip()
            if self._is_header_footer_pattern(line):
                footers.append(line)
                content_lines[i] = ''
        
        cleaned_text = '\n'.join([line for line in content_lines if line.strip()])
        return cleaned_text, headers, footers
    
    def _is_header_footer_pattern(self, text: str) -> bool:
        """헤더/푸터 패턴을 감지합니다."""
        if not text or len(text.strip()) < 3:
            return False
        
        # 페이지 번호 패턴
        if re.match(r'^\s*\d+\s*$', text):
            return True
        
        # 날짜 패턴
        if re.search(r'\d{4}[-/]\d{1,2}[-/]\d{1,2}', text):
            return True
        
        # 짧고 반복될 가능성이 높은 텍스트
        if len(text.strip()) < 50 and (
            'page' in text.lower() or 
            'chapter' in text.lower() or
            'section' in text.lower() or
            '©' in text or
            'copyright' in text.lower()
        ):
            return True
        
        return False
    
    def _extract_tables(self, page) -> List[Dict[str, Any]]:
        """테이블 정보를 추출합니다."""
        tables = []
        try:
            # PyMuPDF의 테이블 추출 기능 사용
            tabs = page.find_tables()
            for i, tab in enumerate(tabs):
                table_data = {
                    'table_id': f"table_{i}",
                    'bbox': tab.bbox,  # 테이블 위치
                    'rows': tab.extract(),  # 테이블 데이터
                    'summary': self._generate_table_summary(tab.extract())
                }
                tables.append(table_data)
        except:
            # 테이블 추출 실패 시 텍스트 기반 테이블 감지
            tables = self._detect_text_tables(page.get_text())
        
        return tables
    
    def _generate_table_summary(self, table_data: List[List[str]]) -> str:
        """테이블의 요약 설명을 생성합니다."""
        if not table_data or len(table_data) < 2:
            return "Empty table"
        
        headers = table_data[0] if table_data[0] else ["Column " + str(i) for i in range(len(table_data[0]))]
        row_count = len(table_data) - 1
        col_count = len(headers)
        
        return f"Table with {row_count} rows and {col_count} columns. Headers: {', '.join(headers[:3])}{'...' if len(headers) > 3 else ''}"
    
    def _detect_text_tables(self, text: str) -> List[Dict[str, Any]]:
        """텍스트에서 테이블 형태를 감지합니다."""
        tables = []
        lines = text.split('\n')
        
        for i, line in enumerate(lines):
            # 탭이나 여러 공백으로 구분된 컬럼이 있는 경우
            if '\t' in line or re.search(r'\s{3,}', line):
                # 연속된 유사한 패턴의 라인들을 찾아 테이블로 인식
                table_lines = [line]
                j = i + 1
                while j < len(lines) and ('\t' in lines[j] or re.search(r'\s{3,}', lines[j])):
                    table_lines.append(lines[j])
                    j += 1
                
                if len(table_lines) >= 2:  # 최소 2줄 이상
                    tables.append({
                        'table_id': f"text_table_{len(tables)}",
                        'lines': table_lines,
                        'summary': f"Text table with {len(table_lines)} rows detected"
                    })
        
        return tables
    
    def _extract_image_info(self, page) -> List[Dict[str, Any]]:
        """이미지 정보를 추출합니다."""
        images = []
        try:
            image_list = page.get_images()
            for i, img in enumerate(image_list):
                images.append({
                    'image_id': f"image_{i}",
                    'bbox': page.get_image_bbox(img),
                    'size': f"{img[2]}x{img[3]}",  # width x height
                    'description': f"Image {i+1} on page"
                })
        except:
            pass
        
        return images
    
    def _extract_sections(self, blocks: Dict) -> List[Dict[str, Any]]:
        """섹션 제목을 추출합니다."""
        sections = []
        
        for block in blocks.get('blocks', []):
            if block.get('type') == 0:  # 텍스트 블록
                for line in block.get('lines', []):
                    for span in line.get('spans', []):
                        text = span.get('text', '').strip()
                        font_size = span.get('size', 0)
                        font_flags = span.get('flags', 0)
                        
                        # 제목/섹션 헤더 감지 (큰 폰트, 볼드체 등)
                        if (font_size > 12 and 
                            (font_flags & 2**4 or font_flags & 2**6) and  # bold or italic
                            len(text) < 100 and 
                            text and 
                            not text.endswith('.')):
                            
                            sections.append({
                                'text': text,
                                'font_size': font_size,
                                'is_bold': bool(font_flags & 2**4),
                                'bbox': span.get('bbox')
                            })
        
        return sections
    
    def _create_documents_from_page(self, page_data: Dict[str, Any]) -> List[Document]:
        """페이지 데이터에서 Document 객체들을 생성합니다."""
        documents = []
        
        # 메인 텍스트 문서 생성
        if page_data['text']:
            # 향상된 메타데이터 생성
            metadata = {
                'source': page_data['filename'],
                'page': page_data['page_num'],
                'content_type': 'text',
                'sections': [s['text'] for s in page_data['sections']],
                'has_tables': len(page_data['tables']) > 0,
                'has_images': len(page_data['images']) > 0,
                'table_count': len(page_data['tables']),
                'image_count': len(page_data['images'])
            }
            
            # 섹션 정보가 있으면 추가
            if page_data['sections']:
                metadata['main_section'] = page_data['sections'][0]['text']
            
            doc = Document(
                page_content=page_data['text'],
                metadata=metadata
            )
            documents.append(doc)
        
        # 테이블 문서들 생성
        for table in page_data['tables']:
            table_metadata = {
                'source': page_data['filename'],
                'page': page_data['page_num'],
                'content_type': 'table',
                'table_id': table['table_id'],
                'table_summary': table['summary']
            }
            
            # 테이블 내용을 텍스트로 변환
            if 'rows' in table:
                table_text = self._table_to_text(table['rows'])
            else:
                table_text = '\n'.join(table.get('lines', []))
            
            if table_text.strip():
                doc = Document(
                    page_content=f"Table: {table['summary']}\n\n{table_text}",
                    metadata=table_metadata
                )
                documents.append(doc)
        
        # 이미지 설명 문서들 생성
        for image in page_data['images']:
            image_metadata = {
                'source': page_data['filename'],
                'page': page_data['page_num'],
                'content_type': 'image',
                'image_id': image['image_id'],
                'image_size': image['size']
            }
            
            doc = Document(
                page_content=f"Image description: {image['description']} (Size: {image['size']})",
                metadata=image_metadata
            )
            documents.append(doc)
        
        return documents
    
    def _table_to_text(self, rows: List[List[str]]) -> str:
        """테이블 데이터를 텍스트로 변환합니다."""
        if not rows:
            return ""
        
        text_lines = []
        for row in rows:
            if row:  # 빈 행이 아닌 경우
                text_lines.append(" | ".join([str(cell) for cell in row if cell]))
        
        return "\n".join(text_lines)
    
    def _apply_semantic_chunking(self, documents: List[Document]) -> List[Document]:
        """의미 단위로 문서를 재분할합니다."""
        semantic_documents = []
        
        for doc in documents:
            if doc.metadata.get('content_type') == 'text':
                # 텍스트 문서만 semantic chunking 적용
                chunks = self._semantic_split(doc.page_content, doc.metadata)
                semantic_documents.extend(chunks)
            else:
                # 테이블, 이미지 등은 그대로 유지
                semantic_documents.append(doc)
        
        return semantic_documents
    
    def _semantic_split(self, text: str, base_metadata: Dict) -> List[Document]:
        """텍스트를 의미 단위로 분할합니다."""
        # 먼저 문장 단위로 분할
        sentences = self._split_into_sentences(text)
        
        if len(sentences) <= 1:
            return [Document(page_content=text, metadata=base_metadata)]
        
        # 문장들의 임베딩 계산
        try:
            embeddings = self._get_sentence_embeddings(sentences)
            
            # 의미적 유사성을 기반으로 청크 생성
            chunks = self._create_semantic_chunks(sentences, embeddings, base_metadata)
            
            return chunks
            
        except Exception:
            # 임베딩 실패 시 기본 분할 방식 사용
            fallback_splitter = RecursiveCharacterTextSplitter(
                chunk_size=settings.CHUNK_SIZE,
                chunk_overlap=settings.CHUNK_OVERLAP
            )
            fallback_docs = fallback_splitter.split_documents([Document(page_content=text, metadata=base_metadata)])
            return fallback_docs
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """텍스트를 문장 단위로 분할합니다."""
        # 간단한 문장 분할 (한국어/영어 고려)
        sentences = re.split(r'[.!?]\s+|[。！？]\s*', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        return sentences
    
    def _get_sentence_embeddings(self, sentences: List[str]) -> np.ndarray:
        """문장들의 임베딩을 계산합니다."""
        if self.embeddings is None:
            raise Exception("Embeddings not initialized")
        
        # 배치로 임베딩 계산 (효율성)
        embeddings = self.embeddings.embed_documents(sentences)
        return np.array(embeddings)
    
    def _create_semantic_chunks(self, sentences: List[str], embeddings: np.ndarray, base_metadata: Dict) -> List[Document]:
        """의미적 유사성을 기반으로 청크를 생성합니다."""
        chunks = []
        current_chunk = []
        current_chunk_size = 0
        
        for i, sentence in enumerate(sentences):
            sentence_len = len(sentence)
            
            # 현재 청크가 비어있으면 첫 문장 추가
            if not current_chunk:
                current_chunk.append(sentence)
                current_chunk_size = sentence_len
                continue
            
            # 최대 크기 초과 시 청크 완성
            if current_chunk_size + sentence_len > settings.SEMANTIC_CHUNK_MAX_SIZE:
                if current_chunk_size >= settings.SEMANTIC_CHUNK_MIN_SIZE:
                    chunks.append(self._create_chunk_document(current_chunk, base_metadata, len(chunks)))
                current_chunk = [sentence]
                current_chunk_size = sentence_len
                continue
            
            # 이전 문장과의 유사도 계산
            if i > 0:
                similarity = cosine_similarity(
                    embeddings[i-1:i], 
                    embeddings[i:i+1]
                )[0][0]
                
                # 유사도가 임계값 이상이면 같은 청크에 추가
                if similarity >= settings.SENTENCE_SIMILARITY_THRESHOLD:
                    current_chunk.append(sentence)
                    current_chunk_size += sentence_len
                else:
                    # 유사도가 낮으면 새 청크 시작
                    if current_chunk_size >= settings.SEMANTIC_CHUNK_MIN_SIZE:
                        chunks.append(self._create_chunk_document(current_chunk, base_metadata, len(chunks)))
                    current_chunk = [sentence]
                    current_chunk_size = sentence_len
            else:
                current_chunk.append(sentence)
                current_chunk_size += sentence_len
        
        # 마지막 청크 처리
        if current_chunk and current_chunk_size >= settings.SEMANTIC_CHUNK_MIN_SIZE:
            chunks.append(self._create_chunk_document(current_chunk, base_metadata, len(chunks)))
        
        return chunks if chunks else [Document(page_content=' '.join(sentences), metadata=base_metadata)]
    
    def _create_chunk_document(self, sentences: List[str], base_metadata: Dict, chunk_id: int) -> Document:
        """청크 문서를 생성합니다."""
        chunk_text = ' '.join(sentences)
        chunk_metadata = base_metadata.copy()
        chunk_metadata.update({
            'chunk_id': chunk_id,
            'chunk_type': 'semantic',
            'sentence_count': len(sentences),
            'chunk_size': len(chunk_text)
        })
        
        return Document(page_content=chunk_text, metadata=chunk_metadata)


# 전역 인스턴스
enhanced_processor = EnhancedDocumentProcessor()