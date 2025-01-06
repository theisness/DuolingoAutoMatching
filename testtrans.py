# test googletrans

from googletrans import Translator
import asyncio
from typing import Optional

class AsyncTranslator:
    def __init__(self, proxy: str = "http://127.0.0.1:7890"):
        self.proxy = proxy
        self.translator: Optional[Translator] = None
        
    async def __aenter__(self):
        self.translator = Translator(proxy=self.proxy)
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.translator:
            await self.translator.client.aclose()
            
    async def translate_text(self, text: str, src: str = 'zh-cn', dest: str = 'en') -> Optional[str]:
        """
        Translate text using Google Translate
        Args:
            text: Text to translate
            src: Source language (default: zh-cn)
            dest: Destination language (default: en)
        Returns:
            Translated text or None if translation fails
        """
        if not self.translator:
            self.translator = Translator(proxy=self.proxy)
            
        try:
            result = await self.translator.translate(text, src=src, dest=dest)
            return result.text
        except Exception as e:
            print(f"Translation error: {str(e)}")
            return None

# Example usage
async def test_translate():
    async with AsyncTranslator() as translator:
        result = await translator.translate_text("你好，世界！")
        print(f"Original: 你好，世界！")
        print(f"Translated: {result}")

def main():
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(test_translate())
    finally:
        loop.close()

if __name__ == "__main__":
    main()