"""Fake HUG API module usable for testing importation of modules"""
import hug

@hug.get()
async def made_up_api():
    return 'made_up'
