import time
from worker import celery
from app.extensions import db
from app.models.prompt import PromptRequest, PromptStatus


@celery.task
def process_prompt_task(prompt_id):

    prompt = PromptRequest.query.get(prompt_id)

    if not prompt:
        return
    
    try:

        prompt.status = PromptStatus.PROCESSING
        db.session.commit()

        #simulation
        time.sleep(5)

        prompt.status = PromptStatus.COMPLETED
        prompt.result_path = "files/result.glb"
        prompt.error_message = None
        db.session.commit()
    
    except Exception as e:
        prompt.status = PromptStatus.FAILED
        prompt.error_message = str(e)
        db.session.commit()