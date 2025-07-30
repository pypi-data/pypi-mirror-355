from hie_rag.process import Process
from hie_rag.split import Split
from hie_rag.utils import Utils


class SplitAndProcess:
    def __init__(self, base_url: str):
        self.split = Split(base_url=base_url)
        self.utils = Utils(base_url=base_url)
        self.process = Process(base_url=base_url)

    def split_and_process(self, uploaded_file):
        extracted_text = self.utils.extract_text(uploaded_file)
        result_split = self.split.split(extracted_text)
        result_process = self.process.process_chunks(result_split)

        return result_process