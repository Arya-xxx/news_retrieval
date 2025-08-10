from flask import Blueprint, request, jsonify
from app.db.repositories import news_repository
from app.utils.redis_cache import cache

news_bp = Blueprint('news', __name__, url_prefix='/api/v1/news')

@news_bp.route('/category', methods=['GET'])
@cache.cache_response()
def get_by_category():
    try:
        category = request.args.get('category')
        if not category:
            return jsonify({"error": "Category name is required"}), 422
        
        limit = int(request.args.get('limit', 5))
        articles = news_repository.get_articles_by_category(category, limit)
        
        return jsonify({
            "meta": {
                "generated": True,
                "count": len(articles)
            },
            "articles": articles
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@news_bp.route('/score', methods=['GET'])
@cache.cache_response()
def get_by_score():
    try:
        min_score = float(request.args.get('min_score', 0.7))
        limit = int(request.args.get('limit', 5))
        
        articles = news_repository.get_articles_by_score(min_score, limit)
        
        return jsonify({
            "meta": {
                "type": "score",
                "generated": True,
                "count": len(articles),
                "min_score": min_score
            },
            "articles": articles
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@news_bp.route('/search', methods=['GET'])
@cache.cache_response()
def search_articles():
    try:
        query = request.args.get('q')
        if not query:
            return jsonify({"error": "Search query is required"}), 400
        
        limit = int(request.args.get('limit', 5))
        articles = news_repository.search_articles(query, limit)
        
        return jsonify({
            "meta": {
                "type": "search",
                "generated": True,
                "count": len(articles),
                "query": query
            },
            "articles": articles
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@news_bp.route('/source', methods=['GET'])
@cache.cache_response()
def get_by_source():
    try:
        source = request.args.get('source')
        if not source:
            return jsonify({"error": "Source is required"}), 400
        
        limit = int(request.args.get('limit', 5))
        articles = news_repository.get_articles_by_source(source, limit)
        
        return jsonify({
            "meta": {
                "type": "source",
                "generated": True,
                "count": len(articles),
                "source": source
            },
            "articles": articles
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@news_bp.route('/nearby', methods=['GET'])
@cache.cache_response()
def get_nearby_articles():
    try:
        lat = request.args.get('lat')
        lon = request.args.get('lon')
        radius_km = float(request.args.get('radius_km', 10))
        
        if not lat or not lon:
            return jsonify({"error": "Latitude and Longitude are required"}), 400
        
        limit = int(request.args.get('limit', 5))
        articles = news_repository.get_articles_nearby(float(lat), float(lon), radius_km, limit)
        
        return jsonify({
            "meta": {
                "type": "nearby",
                "generated": True,
                "count": len(articles),
                "lat": lat,
                "lon": lon,
                "radius_km": radius_km
            },
            "articles": articles
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500