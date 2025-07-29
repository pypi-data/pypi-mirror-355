def success_response(data=None, message="Operación exitosa", status_code=200):
    return {
        "status": "success",
        "message": message,
        "data": data
    }, status_code

def error_response(message="Ocurrió un error", status_code=400):
    return {
        "status": "error",
        "message": message,
        "data": None
    }, status_code
