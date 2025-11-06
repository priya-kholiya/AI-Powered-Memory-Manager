def lru(process_id, memory_size, reference_string, frames):
    memory = []  # To store current pages (most recent at end)
    page_faults = 0
    hits = 0
    steps = []

    for page in reference_string:
        step_info = {"page": page, "action": "", "memory": [], "pageFaultsSoFar": 0, "hitsSoFar": 0}

        if page not in memory:
            # Page Fault → add or replace
            page_faults += 1
            step_info["action"] = "MISS"

            if len(memory) < frames:
                memory.append(page)
            else:
                removed = memory.pop(0)  # remove least recently used
                memory.append(page)
                step_info["replaced"] = removed
        else:
            # Page Hit → move it to the end (most recently used)
            hits += 1
            step_info["action"] = "HIT"
            memory.remove(page)
            memory.append(page)

        step_info["memory"] = memory.copy()
        step_info["pageFaultsSoFar"] = page_faults
        step_info["hitsSoFar"] = hits
        steps.append(step_info)

    return {
        "processId": process_id,
        "hits": hits,
        "pageFaults": page_faults,
        "steps": steps
    }
