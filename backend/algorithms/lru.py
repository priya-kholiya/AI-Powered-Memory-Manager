
def lru(process_id, memory_size, reference_string, frames):
    memory = []  # To store current pages
    page_faults = 0
    steps = []

    for page in reference_string:
        if page not in memory:
          
            if len(memory) < frames:
                memory.append(page)
            else:
                # Remove least recently used (first element)
                
                memory.pop(0)
                memory.append(page)
            page_faults += 1
        else:
            # Page hit → move page to the end to mark as recently used
            memory.remove(page)
            memory.append(page)

        steps.append(memory.copy())

    hits = len(reference_string) - page_faults

    return {
        "processId": process_id,
        "pageFaults": page_faults,
        "hits": hits,
        "steps": steps
    }

