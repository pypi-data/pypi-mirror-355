import sqlite3
import os
from mcp.server import FastMCP

# # 初始化 FastMCP 服务器
app = FastMCP('gaokao-rank')

@app.tool(
    name="get_rank",
    description="""根据高考分数查询省内排名位次
    
    此工具可以根据指定的省份、年份、考试类别和分数，查询该分数在对应省份的排名位次。
    
    参数说明：
    - province: 省份名称，如"北京"、"上海"、"广东"等
    - year: 考试年份标识，可以是纯年份（如"2024"、"2023"）或年份+学历层次组合（如"2024本科"、"2023专科"）
    - category: 考试类别，如"理科"、"文科"、"3+3综合"、"物理类"等
    - score: 高考总分，范围0-750分
    
    返回值：
    - 返回该分数在指定省份、年份、类别下的排名位次（数字越小排名越高）
    
    使用场景：
    - 高考志愿填报参考
    - 分数线预测分析
    - 教育数据统计分析
    
    注意事项：
    - 确保输入的省份、年份、类别在数据库中存在
    - 分数必须在合理范围内（0-750分）
    - 排名基于历史数据，仅供参考
    """
)
async def get_rank(province: str, year: str, category: str, score: int) -> int:
    # 校验province、year和category的合法性
    if not province or not year or not category:
        raise ValueError("省份、年份和类别不能为空")
    
    if score < 0 or score > 750:
        raise ValueError("分数必须在0-750之间")
    
    # 数据库文件路径
    db_path = os.path.join(os.path.dirname(__file__), 'data', 'gaokao.db')
    
    try:
        # 连接数据库
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 根据province、year和category查询t_exam_contexts表，获得主键id
        cursor.execute(
            "SELECT id FROM t_exam_contexts WHERE province = ? AND year = ? AND category = ?",
            (province, year, category)
        )
        result = cursor.fetchone()
        
        if not result:
            raise ValueError(f"未找到对应的考试信息: {province} {year} {category}")
        
        context_id = result[0]
        
        # 根据context_id和score查询t_score_segments，获得省排名
        # 查找包含该分数的分数段
        cursor.execute(
            """SELECT min_order, max_order, min_score, max_score 
               FROM t_score_segments 
               WHERE context_id = ? AND min_score <= ? AND max_score >= ?
               ORDER BY min_score DESC
               LIMIT 1""",
            (context_id, score, score)
        )
        
        segment_result = cursor.fetchone()
        
        if not segment_result:
            # 如果没有找到包含该分数的分数段，查找最接近的分数段
            cursor.execute(
                """SELECT min_order, max_order, min_score, max_score 
                   FROM t_score_segments 
                   WHERE context_id = ? AND min_score <= ?
                   ORDER BY min_score DESC
                   LIMIT 1""",
                (context_id, score)
            )
            segment_result = cursor.fetchone()
            
            if not segment_result:
                # 如果分数太低，返回最低排名
                cursor.execute(
                    """SELECT MAX(max_order) FROM t_score_segments WHERE context_id = ?""",
                    (context_id,)
                )
                max_rank_result = cursor.fetchone()
                return max_rank_result[0] if max_rank_result[0] else 999999
        
        min_order, max_order, min_score, max_score = segment_result
        
        # 如果分数正好在分数段范围内，进行线性插值估算排名
        if min_score <= score <= max_score:
            if min_score == max_score:
                # 分数段内只有一个分数，返回最大排名
                rank = max_order
            else:
                # 线性插值计算排名
                score_ratio = (score - min_score) / (max_score - min_score)
                rank = int(max_order - score_ratio * (max_order - min_order))
        else:
            # 分数高于该分数段，返回该分数段的最高排名
            rank = min_order
        
        conn.close()
        return rank
        
    except sqlite3.Error as e:
        raise RuntimeError(f"数据库查询错误: {str(e)}")
    except Exception as e:
        raise RuntimeError(f"查询排名时发生错误: {str(e)}")

@app.tool(
    name="get_categories",
    description="""根据省份和年份获取所有可用的考试类别
    
    此工具可以根据指定的省份和年份，查询该省份在指定年份下所有可用的考试类别。
    
    参数说明：
    - province: 省份名称，如"北京"、"上海"、"广东"等
    - year: 考试年份标识，可以是纯年份（如"2024"、"2023"）或年份+学历层次组合（如"2024本科"、"2023专科"）
    
    返回值：
    - 返回该省份在指定年份下所有可用考试类别的列表
    
    使用场景：
    - 查询某省某年的考试类别选项
    - 为用户提供可选的考试类别列表
    - 验证考试类别的有效性
    
    注意事项：
    - 确保输入的省份、年份在数据库中存在
    - 返回的类别列表按字母顺序排序
    """
)
async def get_categories(province: str, year: str) -> list[str]:
    # 校验province和year的合法性
    if not province or not year:
        raise ValueError("省份和年份不能为空")
    
    # 数据库文件路径
    db_path = os.path.join(os.path.dirname(__file__), 'data', 'gaokao.db')
    
    try:
        # 连接数据库
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 根据province和year查询t_exam_contexts表，获得所有可用的category
        cursor.execute(
            "SELECT DISTINCT category FROM t_exam_contexts WHERE province = ? AND year = ? ORDER BY category",
            (province, year)
        )
        results = cursor.fetchall()
        
        if not results:
            raise ValueError(f"未找到对应的考试信息: {province} {year}")
        
        # 提取category列表
        categories = [result[0] for result in results]
        
        conn.close()
        return categories
        
    except sqlite3.Error as e:
        raise RuntimeError(f"数据库查询错误: {str(e)}")
    except Exception as e:
        raise RuntimeError(f"查询考试类别时发生错误: {str(e)}")

if __name__ == "__main__":
    app.run(transport='stdio')