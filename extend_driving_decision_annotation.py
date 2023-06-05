import os
import json
import sys
import copy

    
if __name__ == '__main__':
    print("Extend Driving Decision Annotations of PSI 2.0 Dataset.")

    root_path = sys.argv[1]

    key_frame_anotation_path = os.path.join(root_path, 'PSI2.0_TrainVal/annotations/cognitive_annotation_key_frame')
    extended_annotation_path = os.path.join(root_path, 'PSI2.0_TrainVal/annotations/cognitive_annotation_extended')
    cv_annotation_path = os.path.join(root_path, 'PSI2.0_TrainVal/annotations/cv_annotation')

    if not os.path.exists(extended_annotation_path):
        os.makedirs(extended_annotation_path)

    video_list = sorted(os.listdir(key_frame_anotation_path))

    for vname in video_list:
        # 1. load key-frame annotations
        key_dd_ann_file = os.path.join(key_frame_anotation_path, vname, 'driving_decision.json')
        with open(key_dd_ann_file, 'r') as f:
            key_dd_ann = json.load(f)

        # 2. extend annotations (driving decision) - decision to the future frames, description to the prior frames
        extended_dd_ann = copy.deepcopy(key_dd_ann)

        annotator_list = key_dd_ann['frames'][list(key_dd_ann['frames'].keys())[0]]['cognitive_annotation'].keys()
        frame_list = sorted(key_dd_ann['frames'].keys())
        for annotator_k in annotator_list:            
            pivot_speed = "maintainSpeed" # at the beginning no labels, use "goStraight" == "maintainSpeed" == 0
            pivot_direction = "goStraight"
            for i in range(len(frame_list)):
                frame_id = frame_list[i]
                if extended_dd_ann['frames'][frame_id]['cognitive_annotation'][annotator_k]['driving_decision_speed'] == "":
                    extended_dd_ann['frames'][frame_id]['cognitive_annotation'][annotator_k]['driving_decision_speed'] = pivot_speed
                else:
                    pivot_speed = extended_dd_ann['frames'][frame_id]['cognitive_annotation'][annotator_k]['driving_decision_speed']
                if extended_dd_ann['frames'][frame_id]['cognitive_annotation'][annotator_k]['driving_decision_direction'] == "":
                    extended_dd_ann['frames'][frame_id]['cognitive_annotation'][annotator_k]['driving_decision_direction'] = pivot_direction
                else:
                    pivot_direction = extended_dd_ann['frames'][frame_id]['cognitive_annotation'][annotator_k]['driving_decision_direction']
                    
            last_frame_id = frame_list[-1]
            pivot_des = extended_dd_ann['frames'][last_frame_id]['cognitive_annotation'][annotator_k]['explanation']
            for i in range(len(frame_list)-1, -1, -1):
                frame_id = frame_list[i]
                if extended_dd_ann['frames'][frame_id]['cognitive_annotation'][annotator_k]['explanation'] == '':
                    extended_dd_ann['frames'][frame_id]['cognitive_annotation'][annotator_k]['explanation'] = pivot_des
                else:
                    pivot_des = extended_dd_ann['frames'][frame_id]['cognitive_annotation'][annotator_k]['explanation']
                    # Note: after this operation, some frames at the end of the observed frame list do not have descriptions, ['description']== ""  

        # 3. output extended annotations
        output_dir = os.path.join(extended_annotation_path, vname)
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # write json to file
        extended_dd_ann_file = os.path.join(extended_annotation_path, vname, 'driving_decision.json')
        with open(extended_dd_ann_file, 'w') as file:
            json_string = json.dumps(extended_dd_ann, default=lambda o: o.__dict__, sort_keys=False, indent=4)
            file.write(json_string)
