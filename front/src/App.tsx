import PdfUploader from '@/components/PdfUploader';
import ChatBot from '@/components/ChatBot';

function App() {
  return (
    <div className="min-h-screen bg-gray-100">
      <div className="container mx-auto px-4 py-8">
        <h1 className="text-3xl font-bold text-center text-gray-800 mb-8">
          PDF 업로더 & 챗봇
        </h1>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 h-[calc(100vh-150px)]">
          <div className="flex flex-col justify-start">
            <PdfUploader />
          </div>
          <div className="h-full">
            <ChatBot />
          </div>
        </div>
      </div>
    </div>
  );
}

export default App
