from db import get_all_tags

@app.route('/tags', methods=['GET'])
def list_tags():
    result, status_code = get_all_tags()
    return jsonify(result), status_code
