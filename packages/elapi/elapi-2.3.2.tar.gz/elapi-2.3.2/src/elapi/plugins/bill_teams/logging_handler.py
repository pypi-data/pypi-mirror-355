import logging

import sh


class PostfixEmailHandler(logging.Handler):
    def __init__(self):
        super().__init__()

    @staticmethod
    def send_email(email_body: str):
        # noinspection PyUnresolvedReferences
        mail = sh.mail
        mail(
            "-s",
            "Test mail from elAPI bill-team",
            "mahadi.xion@urz.uni-heidelberg.de",
            # "alexander.haller@urz.uni-heidelberg.de",
            _in=sh.echo(email_body),
        )

    def emit(self, record):
        if record.levelno >= 40:
            main_log: str = f"""{record.levelname} at {record.asctime}: {record.msg}"""
            email_body: str = f"""Hi,
            
This is a test message. elAPI has encountered the following error while running {record.funcName} in {record.pathname}.

{main_log}

Best regards,
<eLabFTW Billing Team>
"""
            self.send_email(email_body)
