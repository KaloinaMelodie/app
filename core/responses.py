from fastapi.responses import JSONResponse

def success_response(data=None, message="Success", status_code=200):
    return JSONResponse(
        status_code=status_code,
        content={"status": "success", "message": message,"code": status_code, "data": data}
    )

def error_response(message="Error", status_code=400, detail=None):
    return JSONResponse(
        status_code=status_code,
        content={"status": "error", "message": message, "detail": detail}
    )
