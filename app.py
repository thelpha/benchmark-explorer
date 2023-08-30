from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.requests import Request

import utils
from jinja2 import Environment

app = FastAPI()

raw = utils.get_data()
data_dict, data_list = utils.process_data(utils.process_json(raw))

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")
env = templates.env
env.filters['regex_replace'] = utils.regex_replace

@app.get("/")
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request,"data": data_list})

@app.get("/data")
def get_data():
    return data_dict

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)