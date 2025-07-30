from mcp.server.fastmcp import FastMCP
from core.ragflow_api import get_datasets, get_dataset_documents, create_dataset, create_chunk, retrieve_chunks

mcp = FastMCP("ragflow_mcp")

# 配置参数
ADDRESS = "ragflow.iepose.cn"  # 替换为实际地址
API_KEY = "ragflow-g4ZTU4ZjM4YTAwMTExZWZhZjkyMDI0Mm"  # 替换为实际的API密钥
DATASET_NAME = "第二大脑"
DATASET_ID = "c3303d4ee45611ef9b610242ac180003" # 第二大脑的数据集ID

# @mcp.tool(
#     annotations={
#         "title": "Calculate Sum",
#         "readOnlyHint": True,
#         "openWorldHint": False
#     }
# )
@mcp.tool(name="list_all_documents", description="列出所有数据下的文档")
def list_all_documents(dataset_id = DATASET_ID) -> str:
    """
    列出指定数据集下的所有文档。
    :param dataset_id: 数据集ID，如果未提供则使用默认数据集ID。通常情况下使用默认数据集ID。
    :return: 返回所有文档的名称和ID列表。
    例如：[{"id": "doc1", "name": "文档1"}, {"id": "doc2", "name": "文档2"}]
    """
    raw = get_dataset_documents(
        address=ADDRESS,
        api_key=API_KEY,
        dataset_id=dataset_id,
        page=1,
        page_size=100,  # 设置为100以获取更多文档
        keywords=None,  # 可选参数
        orderby="update_time"
    )
    
    # 解析返回的数据
    if raw and raw.get('code') == 0 and 'data' in raw:
        docs = raw['data'].get('docs', [])
        # 提取文档的ID和名称
        document_list = [{"id": doc['id'], "name": doc['name']} for doc in docs]
        return str(document_list)
    else:
        return "[]"  # 如果没有数据或请求失败，返回空列表

@mcp.tool(name="create_chunk_to_document", description="在指定文档中创建新的文本块")
def create_chunk_to_document(document_id: str, content: str, important_keywords: list = None, dataset_id: str = DATASET_ID) -> str:
    """
    在指定的文档中创建新的文本块(chunk)。
    
    :param document_id: 文档ID，必需参数
    :param content: chunk的文本内容，必需参数
    :param important_keywords: 与chunk相关的关键词列表，可选参数
    :param dataset_id: 数据集ID，如果未提供则使用默认数据集ID
    :return: 返回创建结果的状态信息
    """
    result = create_chunk(
        address=ADDRESS,
        api_key=API_KEY,
        dataset_id=dataset_id,
        document_id=document_id,
        content=content,
        important_keywords=important_keywords
    )
    
    if result and result.get('code') == 0:
        return f"成功创建chunk到文档 {document_id}。chunk内容: {content[:50]}..."
    else:
        error_msg = result.get('message', '未知错误') if result else '请求失败'
        return f"创建chunk失败: {error_msg}"

@mcp.tool(name="search_chunks", description="从数据集中检索相关的文本块")
def search_chunks(question: str, dataset_id: str = DATASET_ID, page_size: int = 5, similarity_threshold: float = 0.1) -> str:
    """
    从指定数据集中检索与问题相关的文本块。
    
    :param question: 要搜索的问题或关键词，必需参数
    :param dataset_id: 数据集ID，如果未提供则使用默认数据集ID
    :param page_size: 返回的最大结果数量，默认为10
    :param similarity_threshold: 相似度阈值，默认为0.2
    :return: 返回检索结果的格式化字符串
    """
    result = retrieve_chunks(
        address=ADDRESS,
        api_key=API_KEY,
        question=question,
        dataset_ids=[dataset_id],
        page=1,
        page_size=page_size,
        similarity_threshold=similarity_threshold,
        vector_similarity_weight=0.5,
        top_k=50,
        keyword=False,  # 启用关键词匹配
        highlight=False  # 启用高亮显示
    )
    
    if result and result.get('code') == 0:
        chunks = result.get('data', {}).get('chunks', [])
        total_count = result.get('data', {}).get('total', len(chunks))
        
        if not chunks:
            return f"未找到与 '{question}' 相关的内容"
        
        # 格式化返回结果
        formatted_results = []
        for i, chunk in enumerate(chunks[:page_size], 1):
            # 优先使用高亮内容，如果没有则使用原始内容
            content = chunk.get('highlight', chunk.get('content', ''))
            similarity = chunk.get('similarity', 0)
            # 修正文档名称字段
            doc_name = chunk.get('document_keyword', chunk.get('document_name', '未知文档'))
            # 获取关键词信息
            keywords = chunk.get('important_keywords', [])
            keywords_str = ', '.join(keywords) if keywords else ''
            
            # 构建结果字符串
            result_str = f"{i}. 【{doc_name}】(相似度: {similarity:.3f})"
            if keywords_str:
                result_str += f"\n关键词: {keywords_str}"
            result_str += f"\n{content[:500]}{'...' if len(content) > 500 else ''}"
            
            formatted_results.append(result_str)
        
        return f"找到 {total_count} 个相关结果（显示前{len(chunks)}个）：\n\n" + "\n\n".join(formatted_results)
    else:
        error_msg = result.get('message', '未知错误') if result else '请求失败'
        return f"检索失败: {error_msg}"

def main():
    # Initialize and run the server
    mcp.run(transport='stdio')

if __name__ == "__main__":
    main()
    # result = list_all_documents()  # 调用示例函数以测试功能
    # print(result)  # 打印结果以验证功能是否正常
