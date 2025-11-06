from queue import Queue

def fifo(process_id, memory_size, reference_string, frames):
    memory_set = set()
    memory_queue = Queue()
    page_faults = 0
    hits = 0
    steps = []

    for page in reference_string:
        step_info = {"page": page, "action": "", "memory": []}

        if page not in memory_set:
            page_faults += 1
            step_info["action"] = "MISS"

            if len(memory_set) < frames:
                memory_set.add(page)
                memory_queue.put(page)
            else:
                removed = memory_queue.get()
                memory_set.remove(removed)
                memory_set.add(page)
                memory_queue.put(page)
                step_info["replaced"] = removed
        else:
            hits += 1
            step_info["action"] = "HIT"

        step_info["memory"] = list(memory_set)
        step_info["pageFaultsSoFar"] = page_faults
        step_info["hitsSoFar"] = hits
        steps.append(step_info)

    return {
        "processId": process_id,
        "hits": hits,
        "pageFaults": page_faults,
        "steps": steps
    }
