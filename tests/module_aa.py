"""Fake HUG API module usable for testing importation of modules"""
import hug

@hug.get()
async def made_up_api(hug_my_directive=True):
    """for testing"""
    return hug_my_directive
