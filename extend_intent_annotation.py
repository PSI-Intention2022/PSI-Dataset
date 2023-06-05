import os
import json
import sys
import copy

def most_frequent(List):
    # return the most frequent intent estimation made by all annotators
    counter = 0
    num = List[0]
    
    for i in List:
        curr_frequency = List.count(i)
        if(curr_frequency> counter):
            counter = curr_frequency
            num = i

    return num

    
if __name__ == '__main__':
    print("Extend Intent Annotations of PSI 2.0 Dataset.")

    root_path = sys.argv[1]

    key_frame_anotation_path = os.path.join(root_path, 'PSI2.0_TrainVal/annotations/cognitive_annotation_key_frame')
    extended_annotation_path = os.path.join(root_path, 'PSI2.0_TrainVal/annotations/cognitive_annotation_extended')
    cv_annotation_path = os.path.join(root_path, 'PSI2.0_TrainVal/annotations/cv_annotation')

    if not os.path.exists(extended_annotation_path):
        os.makedirs(extended_annotation_path)

    video_list = sorted(os.listdir(key_frame_anotation_path))

    for vname in video_list:
        # 1. load key-frame annotations
        key_intent_ann_file = os.path.join(key_frame_anotation_path, vname, 'pedestrian_intent.json')
        with open(key_intent_ann_file, 'r') as f:
            key_intent_ann = json.load(f)

        # 2. extend annotations (intent & description) - intent to the future frames, description to the prior frames
        extended_intent_ann = copy.deepcopy(key_intent_ann)

        for ped_k in key_intent_ann['pedestrians'].keys():
            observed_frames = key_intent_ann['pedestrians'][ped_k]['observed_frames']
            for ann_k in key_intent_ann['pedestrians'][ped_k]['cognitive_annotations'].keys():
                intent_list = key_intent_ann['pedestrians'][ped_k]['cognitive_annotations'][ann_k]['intent']
                key_frame_list = key_intent_ann['pedestrians'][ped_k]['cognitive_annotations'][ann_k]['key_frame']
                description_list = key_intent_ann['pedestrians'][ped_k]['cognitive_annotations'][ann_k]['description']
                assert len(intent_list) == len(key_frame_list) == len(description_list)

                pivot_int = 'not_sure' # 0.5 # at the beginning if no labels, use "not_sure"
                for frame_k in range(len(observed_frames)):
                    if intent_list[frame_k] == "":
                        extended_intent_ann['pedestrians'][ped_k]['cognitive_annotations'][ann_k]['intent'][frame_k] = pivot_int
                    else:
                        pivot_int = intent_list[frame_k]

                pivot_des = description_list[-1]
                for frame_k in range(len(observed_frames)-1, -1, -1):
                    if description_list[frame_k] == "":
                        extended_intent_ann['pedestrians'][ped_k]['cognitive_annotations'][ann_k]['description'][frame_k] = pivot_des
                    else:
                        pivot_des = description_list[frame_k]
                    # Note: after this operation, some frames at the end of the observed frame list do not have descriptions, ['description']== ""  

        # 3. Ignore 'Already-crossed' frames
        for ped_k in extended_intent_ann['pedestrians'].keys():
            observed_frames = extended_intent_ann['pedestrians'][ped_k]['observed_frames']
            last_intents = []
            last_key_frames = []
            for ann_k in extended_intent_ann['pedestrians'][ped_k]['cognitive_annotations'].keys():
                intent_list = extended_intent_ann['pedestrians'][ped_k]['cognitive_annotations'][ann_k]['intent']
                key_frame_list = extended_intent_ann['pedestrians'][ped_k]['cognitive_annotations'][ann_k]['key_frame']
                last_intents.append(intent_list[-1])
                for j in range(len(observed_frames)-1, -1, -1):
                    if key_frame_list[j] != 0:
                        last_key_frames.append(j) # Note! Here 'j' is not the frame number, it's the idx/position of the frame in the 'observed_frame' list
                        break
                    else:
                        continue

            if most_frequent(last_intents) == 'cross': # only apply to the 'cross' cases
                start_box = extended_intent_ann['pedestrians'][ped_k]['cv_annotations']['bboxes'][0]
                last_key_box = extended_intent_ann['pedestrians'][ped_k]['cv_annotations']['bboxes'][max(last_key_frames)]
                end_box = extended_intent_ann['pedestrians'][ped_k]['cv_annotations']['bboxes'][-1]
                if ((last_key_box[0]+last_key_box[2])/2 - 640) * ((end_box[0]+end_box[2])/2 - 640) >= 0:
                    # Situation 1: By the last key-frame annotation, the target pedestrian already crossed the middle line of the ego-view, and is on the same side as the final position.
                    # In such case, we use the last annotated key-frame as the end of "intent estimation" task
                    last_intent_estimate_idx = max(last_key_frames)
                else: # < 0
                    # Situation 2: By the last key-frame annotation, the target pedestrian is at a different position compared to the final observed position.
                    # In such case, we use the moment when the target pedestrian crossed the middle line of the ego-view as the last frame of "intent estimation" task
                    for cur_frame_k in range(max(last_key_frames), len(observed_frames)): # pedestrian could change positions several times, e.g., vehicle is turning. Thus starts from the last key-frame
                        current_box = extended_intent_ann['pedestrians'][ped_k]['cv_annotations']['bboxes'][cur_frame_k]
                        if ((current_box[0]+current_box[2])/2 - 640) * ((end_box[0]+end_box[2])/2 - 640) >= 0:
                            # once the pedestrian crossed the middle line of ego-view, to the same side as the last frame, use this moment as the last intent estimation task frame
                            last_intent_estimate_idx = cur_frame_k
                            break
                        else:
                            continue
                # Cut redundant intent extended annotations that not usable for "intent estimation" task
                del extended_intent_ann['pedestrians'][ped_k]['observed_frames'][last_intent_estimate_idx+1:]
                del extended_intent_ann['pedestrians'][ped_k]['cv_annotations']['bboxes'][last_intent_estimate_idx+1:]
                for ann_k in extended_intent_ann['pedestrians'][ped_k]['cognitive_annotations'].keys():
                    del extended_intent_ann['pedestrians'][ped_k]['cognitive_annotations'][ann_k]['intent'][last_intent_estimate_idx+1:]
                    del extended_intent_ann['pedestrians'][ped_k]['cognitive_annotations'][ann_k]['key_frame'][last_intent_estimate_idx+1:]
                    del extended_intent_ann['pedestrians'][ped_k]['cognitive_annotations'][ann_k]['description'][last_intent_estimate_idx+1:]


        # 4. output extended annotations
        output_dir = os.path.join(extended_annotation_path, vname)
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # write json to file
        extended_intent_ann_file = os.path.join(extended_annotation_path, vname, 'pedestrian_intent.json')
        with open(extended_intent_ann_file, 'w') as file:
            json_string = json.dumps(extended_intent_ann, default=lambda o: o.__dict__, sort_keys=False, indent=4)
            file.write(json_string)

        print(vname, ": Original observed frames: {} --> valid intent estimation frames: {}".format(
            len(key_intent_ann['pedestrians'][ped_k]['observed_frames']),
            len(extended_intent_ann['pedestrians'][ped_k]['observed_frames'])
        ))
