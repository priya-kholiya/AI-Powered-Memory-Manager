def optimal(process_id, memory_size, reference_string, frames):
    memory = []
    page_faults = 0
    hits = 0
    steps = []
    n = len(reference_string)

    for i in range(n):
        page = reference_string[i]
        step_info = {"page": page, "action": "", "memory": [], "pageFaultsSoFar": 0, "hitsSoFar": 0}

        if page not in memory:
            page_faults += 1
            step_info["action"] = "MISS"

            if len(memory) < frames:
                memory.append(page)
            else:
                # Find page to replace → the one used farthest in the future
                farthest = -1
                replace_index = -1
                for j in range(len(memory)):
                    if memory[j] not in reference_string[i + 1:]:
                        replace_index = j
                        break
                    else:
                        next_use = reference_string[i + 1:].index(memory[j])
                        if next_use > farthest:
                            farthest = next_use
                            replace_index = j

                removed = memory[replace_index]
                memory[replace_index] = page
                step_info["replaced"] = removed
        else:
            hits += 1
            step_info["action"] = "HIT"

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
