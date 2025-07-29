from PyPDF2 import PdfReader, PdfWriter
from byzh_core.Bos import b_makedir
def b_sort_pdf1(file_path, out_path, order: list[int]):
    '''
    :param file_path:
    :param out_path:
    :param order: [1,5,4,3,2]
    :return:
    '''
    # 加载原始 PDF 文件
    reader = PdfReader(file_path)
    writer = PdfWriter()

    if len(order)!= len(reader.pages):
        raise ValueError(f"len(order)={len(order)} 与 len(PDF)={len(reader.pages)} 不匹配！")

    order = [i - 1 for i in order]

    # 添加页面到新 PDF 中
    for i in order:
        writer.add_page(reader.pages[i])

    # 保存到新文件
    b_makedir(out_path)
    with open(out_path, "wb") as f:
        writer.write(f)

def b_sort_pdf2(file_path, out_path, order: list[int | tuple[int, int]]):
    '''
    :param file_path:
    :param out_path:
    :param order: [1, (98, 118), (2, 97), (119, 168)] 或 [1, (98, 118)]
    :return:
    '''
    reader = PdfReader(file_path)
    remain_order = [i+1 for i in range(len(reader.pages))]

    new_order = []
    for element in order:
        if isinstance(element, int):
            new_order.append(element)
            remain_order[element-1] = -1
        elif isinstance(element, tuple):
            for num in range(element[0], element[1]+1):
                new_order.append(num)
                remain_order[num-1] = -1

    remain_order = [i for i in remain_order if i != -1]

    new_order.extend(remain_order)

    b_sort_pdf1(file_path, out_path, new_order)

if __name__ == '__main__':
    b_sort_pdf2("扫描件_20250612(2).pdf", 'out.pdf', [1, (98, 118)])