from ytbotapp import app
from multiprocessing import Pool, Process
# from ytbotapp.classes import Scanner
# import json
# from time import sleep
# import asyncio
# from concurrent.futures import ProcessPoolExecutor



if __name__=='__main__':
    app.run(host='0.0.0.0', port=8000)