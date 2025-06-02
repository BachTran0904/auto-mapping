from fastapi import FastAPI, UploadFile, File, HTTPException
import logging, os, tempfile, subprocess, uvicorn, zipfile, requests, json
from fastapi.responses import JSONResponse, FileResponse
from pathlib import Path
from typing import List
import create_report

app = FastAPI()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@app.post("/upload")
async def upload_and_process(file: UploadFile = File(...), form: UploadFile = File(...)):
    temp_file_path = None 
    temp_file_form_path = None
    #attribute_json = os.path.abspath('attribute.json')  # Use absolute path

    try:
        # Process all uploaded files
        with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        # Process the form file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as temp_file_form:
            content = await form.read()
            temp_file_form.write(content)
            temp_file_form_path = temp_file_form.name
                
        # Build the command - note the order of arguments must match what mapping.py expects
        command = ["python", "mapping.py", temp_file_path, temp_file_form_path]
        logger.info(f"Running command: {' '.join(command)}")
        
        result = subprocess.run(
            command,
            capture_output=True,
            text=True
        )
        
        # Clean up the temporary input files
        if temp_file_path and os.path.exists(temp_file_path):
            os.unlink(temp_file_path)            

        if result.returncode != 0:
            logger.error(f"Script failed with error: {result.stderr}")
            logger.error(f"Script output: {result.stdout}")
            raise HTTPException(status_code=400, detail=f"Script error: {result.stderr or 'No error message'}")
            
        # Return the processed file for download
        return FileResponse(
            temp_file_form_path,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            filename="ZZZ_processed_file.xlsx"
        )
        
    except Exception as e:
        if temp_file_path and os.path.exists(temp_file_path):
            os.unlink(temp_file_path)
        if temp_file_form_path and os.path.exists(temp_file_form_path):
            os.unlink(temp_file_form_path)
        logger.error(f"Error in processing: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/get")
async def getOutput():
    output = "Form.xlsx"
    return output

@app.post("/report")
async def compileReport(proccessed: UploadFile = File(...), report_form: UploadFile = File(...)):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as temp_file:
        content = await proccessed.read()
        temp_file.write(content)
        temp_file_path = temp_file.name

    with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as temp_report_file:
        content = await report_form.read()  # <-- fix here
        temp_report_file.write(content)
        temp_report_file_path = temp_report_file.name

    response = create_report.create_report(temp_file_path, temp_report_file_path)
    
    return FileResponse(
        response,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename="report.xlsx"
    )

# Add this block to run the application
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
