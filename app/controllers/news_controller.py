from flask import Blueprint, request, jsonify
from app.db.repositories import news_repository

news_bp = Blueprint('news', __name__, url_prefix='/api/v1/news')

@news_bp.route('/category', methods=['GET'])
def get_by_category():
    try:
        category = request.args.get('name')
        if not category:
            return jsonify({"error": "Category name is required"}), 400
        
        limit = int(request.args.get('limit', 5))
        articles = news_repository.get_articles_by_category(category, limit)
        
        return jsonify({
            "meta": {
                "generated": True,  # Indicates LLM-generated content
                "count": len(articles)
            },
            "articles": articles
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500