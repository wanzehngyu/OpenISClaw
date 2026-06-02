"""
IS Theory Matcher - Semantic matching engine for IS theories
基于关键词权重 + TF-IDF相似度的匹配引擎
"""

import json
import re
from typing import List, Dict, Optional
from math import sqrt

# ============================================================
# 轻量级中文分词器（无需外部依赖）
# ============================================================

def tokenize_chinese(text: str) -> set:
    """
    简单中文分词：基于字符n-gram + 常见词匹配
    返回词集合（去重）
    """
    # 转小写
    text = text.lower()
    
    # 常见中文词列表（用于简单匹配）
    common_words = [
        '政策', '影响', '行业', '变革', '转型', '创新', '技术', '采纳', '接受',
        '用户', '使用', '系统', '信息', '网络', '平台', '数据', '分析',
        '组织', '企业', '绩效', '竞争优势', '资源', '能力', '知识',
        '制度', '环境', '市场', '竞争', '监管', '合规', '合法',
        '临界', '临界量', '临界点', '规模', '增长', '扩散', '传播',
        '动态', '变化', '调整', '重构', '整合', '构建',
        '感知', '有用', '易用', '有用性', '易用性',
        '行为', '意向', '态度', '规范', '控制', '信念',
        '质量', '满意', '成功', '效果', '效率',
        '权力', '控制', '治理', '歧视', '透明', '问责',
        '可供性', '供给', '行动', '实现', '感知',
        '正常化', '嵌入', '整合', '持续',
        '制度压力', '合法性', '模仿', '同构', '脱耦',
        '网络效应', '外部性', '梅特卡夫', '锁定',
        '虚拟', '远程', '团队', '协作', '信任',
        '事件', '危机', '冲击', '颠覆', '洗牌',
        '稳定', '间断', '突变', '渐进', '激进',
        '学习', '转移', '创造', '编码', '吸收',
        '冗余', '吸收', '高层', '团队', '更替',
        '事件研究', '断点', 'RDD', '双重差分', 'DID',
        '面板', '回归', '工具变量', 'IV',
        'SEM', '结构方程', '因子分析',
        '中介', '调节', '门槛', 'PSM',
        '事件史', 'S型曲线', '扩散模型',
    ]
    
    words = set()
    
    # 提取2-4字词
    for length in [2, 3, 4]:
        for i in range(len(text) - length + 1):
            word = text[i:i+length]
            if word in common_words or re.match(r'[\u4e00-\u9fff]+', word):
                words.add(word)
    
    # 英文分词
    english_words = re.findall(r'[a-z]+', text)
    words.update(english_words)
    
    return words


def tokenize_english(text: str) -> set:
    """英文分词：转小写后按空格和标点分割"""
    text = text.lower()
    # 移除非字母数字字符，分割
    tokens = re.split(r'[\s\.,;:!?\'\"\(\)\[\]\{\}\+\-\*\/\=\<\>]+', text)
    return set(t for t in tokens if len(t) > 1)


def tokenize(text: str) -> set:
    """通用分词：同时处理中英文"""
    return tokenize_chinese(text) | tokenize_english(text)


# ============================================================
# TF-IDF 计算
# ============================================================

def compute_tf(tokens: set, all_tokens: List[set]) -> Dict[str, float]:
    """计算每个token的TF（文档频率）"""
    tf = {}
    total_docs = len(all_tokens)
    for token in tokens:
        df = sum(1 for doc_tokens in all_tokens if token in doc_tokens)
        tf[token] = df / total_docs if total_docs > 0 else 0
    return tf


def tfidf_score(query_tokens: set, doc_tokens: set, idf: Dict[str, float]) -> float:
    """计算query和doc之间的TF-IDF相似度"""
    score = 0.0
    for token in query_tokens:
        if token in doc_tokens:
            tf = 1  # 简化：出现即为1
            idf_val = idf.get(token, 1.0)  # 默认1.0
            score += tf * idf_val
    return score


# ============================================================
# 关键词匹配得分
# ============================================================

def keyword_match_score(query_tokens: set, theory: dict) -> float:
    """
    计算查询与理论的关键词匹配得分
    
    考虑三个层次的匹配：
    1. matching_keywords（最高权重）
    2. key_concepts（中等权重）
    3. typical_phenomena（较低权重）
    """
    # 提取理论关键词
    matching_kws = set(tokenize(' '.join(theory.get('matching_keywords', []))))
    key_concepts = set(tokenize(' '.join(theory.get('key_concepts', []))))
    typical_phen = set(tokenize(' '.join(theory.get('typical_phenomena', []))))
    
    # 计算各层重叠
    match_layer1 = len(query_tokens & matching_kws)  # matching_keywords
    match_layer2 = len(query_tokens & key_concepts)   # key_concepts
    match_layer3 = len(query_tokens & typical_phen)   # typical_phenomena
    
    # 加权求和
    score = (
        match_layer1 * 10.0 +   # 匹配关键词最高权重
        match_layer2 * 5.0 +    # 关键概念中等权重
        match_layer3 * 2.0       # 典型现象较低权重
    )
    
    # 归一化（除以理论关键词总数）
    total_kw_count = len(matching_kws) + len(key_concepts) + len(typical_phen)
    if total_kw_count > 0:
        score = score / sqrt(total_kw_count)  # 用sqrt避免过大差异
    
    return min(score, 100)  # 上限100


def semantic_similarity_score(query_tokens: set, theory: dict) -> float:
    """
    计算语义相似度得分
    考虑：中英文互译、上下位概念
    """
    score = 0.0
    
    # matching_keywords
    matching_kws = set(tokenize(' '.join(theory.get('matching_keywords', []))))
    overlap = len(query_tokens & matching_kws)
    score += overlap * 8
    
    # key_concepts
    key_concepts = set(tokenize(' '.join(theory.get('key_concepts', []))))
    overlap = len(query_tokens & key_concepts)
    score += overlap * 5
    
    # typical_phenomena
    typical_phen = set(tokenize(' '.join(theory.get('typical_phenomena', []))))
    overlap = len(query_tokens & typical_phen)
    score += overlap * 3
    
    # 归一化
    return min(score * 2, 100)


# ============================================================
# 核心匹配函数
# ============================================================

def load_theory_db(db_path: str = None) -> List[dict]:
    """加载理论数据库"""
    if db_path is None:
        import os
        db_path = os.path.join(os.path.dirname(__file__), 'theory_db.json')
    
    with open(db_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data['theories']


def match_theory(
    phenomenon_description: str,
    top_k: int = 3,
    db_path: str = None,
    min_score: float = 0
) -> List[dict]:
    """
    将用户描述的现象与理论数据库进行匹配，返回top-k最匹配的理论
    
    Args:
        phenomenon_description: 用户描述的现象或研究问题
        top_k: 返回前k个最匹配的理论
        db_path: theory_db.json路径
        min_score: 最低分数阈值（低于此分数的理论被过滤）
    
    Returns:
        list of dict，每个元素包含：
        - theory info
        - match_score (0-100)
        - matching_reasons（为什么这个理论匹配）
        - suggested_variables（建议收集哪些变量）
        - recommended_methods（推荐使用的实证方法）
    """
    theories = load_theory_db(db_path)
    
    # 分词
    query_tokens = tokenize(phenomenon_description)
    
    if not query_tokens:
        return []
    
    # 计算每个理论与查询的匹配度
    results = []
    
    # 预计算IDF（简化版：使用理论数量作为总文档数）
    n_theories = len(theories)
    
    for theory in theories:
        # 计算各层得分
        kw_score = keyword_match_score(query_tokens, theory)
        sem_score = semantic_similarity_score(query_tokens, theory)
        
        # 综合得分（加权平均）
        final_score = kw_score * 0.6 + sem_score * 0.4
        
        # 计算matching_reasons
        matching_reasons = _generate_matching_reasons(query_tokens, theory)
        
        # 计算suggested_variables
        suggested_variables = _generate_suggested_variables(theory)
        
        # 计算recommended_methods
        recommended_methods = theory.get('recommended_methods', [])
        
        results.append({
            'theory': theory,
            'match_score': round(final_score, 1),
            'matching_reasons': matching_reasons,
            'suggested_variables': suggested_variables,
            'recommended_methods': recommended_methods
        })
    
    # 排序
    results.sort(key=lambda x: x['match_score'], reverse=True)
    
    # 过滤低分结果
    if min_score > 0:
        results = [r for r in results if r['match_score'] >= min_score]
    
    # 返回top-k
    return results[:top_k]


def _generate_matching_reasons(query_tokens: set, theory: dict) -> List[str]:
    """生成为什么该理论匹配的说明"""
    reasons = []
    
    matching_kws = set(tokenize(' '.join(theory.get('matching_keywords', []))))
    matched_kws = query_tokens & matching_kws
    if matched_kws:
        reasons.append(f"关键词匹配：{'、'.join(list(matched_kws)[:5])}")
    
    key_concepts = set(tokenize(' '.join(theory.get('key_concepts', []))))
    matched_concepts = query_tokens & key_concepts
    if matched_concepts:
        reasons.append(f"概念重叠：{'、'.join(list(matched_concepts)[:3])}")
    
    typical_phen = set(tokenize(' '.join(theory.get('typical_phenomena', []))))
    matched_phen = query_tokens & typical_phen
    if matched_phen:
        reasons.append(f"典型现象：{'、'.join(list(matched_phen)[:3])}")
    
    if not reasons:
        reasons.append(f"理论核心主张（{theory.get('name_zh')}）：{theory.get('core_claim', '')[:50]}...")
    
    return reasons


def _generate_suggested_variables(theory: dict) -> Dict[str, List[str]]:
    """生成变量建议"""
    var_hints = theory.get('variables_hints', {})
    
    result = {}
    for var_type in ['dependent', 'independent', 'mediators', 'moderators']:
        if var_type in var_hints:
            result[var_type] = var_hints[var_type]
    
    return result


def get_theory_by_id(theory_id: str, db_path: str = None) -> Optional[dict]:
    """根据理论ID获取理论信息"""
    theories = load_theory_db(db_path)
    for t in theories:
        if t['id'] == theory_id:
            return t
    return None


def list_all_theories(db_path: str = None) -> List[dict]:
    """列出所有理论"""
    theories = load_theory_db(db_path)
    return [
        {
            'id': t['id'],
            'name_zh': t['name_zh'],
            'name_en': t['name_en'],
            'core_claim': t['core_claim']
        }
        for t in theories
    ]


# ============================================================
# 命令行测试
# ============================================================

if __name__ == '__main__':
    # 测试
    test_descriptions = [
        "政策突然变化导致行业格局发生重大变革",
        "企业引入新系统后员工不愿意使用",
        "平台用户增长达到临界点后呈爆发式增长",
        "远程工作环境下团队协作效率如何提升",
        "企业数字化转型中如何保持竞争优势"
    ]
    
    print("=" * 60)
    print("IS Theory Matcher 测试")
    print("=" * 60)
    
    for desc in test_descriptions:
        print(f"\n现象描述: {desc}")
        print("-" * 40)
        
        results = match_theory(desc, top_k=3)
        
        for i, r in enumerate(results, 1):
            theory = r['theory']
            print(f"\n{i}. {theory['name_zh']} ({theory['name_en']})")
            print(f"   匹配得分: {r['match_score']:.1f}/100")
            print(f"   匹配理由: {'; '.join(r['matching_reasons'][:2])}")
            print(f"   推荐方法: {'、'.join(r['recommended_methods'][:2])}")
    
    print("\n" + "=" * 60)