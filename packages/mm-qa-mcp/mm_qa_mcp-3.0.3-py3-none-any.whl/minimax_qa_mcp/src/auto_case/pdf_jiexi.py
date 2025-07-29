import pdfplumber
import warnings
import re
warnings.filterwarnings("ignore")
def read_pdf_text(pdf_path):
    """
    读取指定路径的PDF文件内容，返回所有文本内容的字符串。
    :param pdf_path: PDF文件的本地路径
    :return: PDF中的全部文本内容
    """
    all_text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            all_text += page.extract_text() or ""
    # 清除特殊不可见字符
    all_text = re.sub(r'[\x00-\x1F\x7F]', '', all_text)
    # all_text = clean_encoding(all_text)
    return all_text

# def clean_encoding(text):
#     # 先转换为bytes，再解码回字符串
#     text_bytes = text.encode('utf-8', errors='ignore')
#     cleaned_text = text_bytes.decode('utf-8')
#     return cleaned_text
if __name__ == "__main__":
    pdf_path = "创作输入框改版.pdf"
    text = read_pdf_text(pdf_path)
    print(text)
