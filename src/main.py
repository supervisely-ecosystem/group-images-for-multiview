import os
from dotenv import load_dotenv
import supervisely as sly
from collections import defaultdict
from typing import List, Dict, Tuple

# load ENV variables for debug
# has no effect in production
if sly.is_development:
    load_dotenv(os.path.expanduser("~/supervisely.env"))
    load_dotenv("local.env")

grouping_mode = os.environ["modal.state.selectOption"]
batch_size = int(os.environ["modal.state.sliderValue"])


def get_grouped_dict(
    image_ids: List[int], anns: List[sly.Annotation]
) -> Dict[str, List[Tuple[int, sly.Annotation]]]:
    if grouping_mode == "by-batches":
        return {"group": list(zip(image_ids, anns))}
    grouped_dict = defaultdict(list)

    for image_id, ann in zip(image_ids, anns):
        entry = (image_id, ann)
        if grouping_mode == "obj-class":
            for label in ann.labels:
                if entry not in grouped_dict[label.obj_class.name]:
                    grouped_dict[label.obj_class.name].append(entry)
        elif grouping_mode == "tags":
            for tag in ann.img_tags:
                if entry not in grouped_dict[tag.name]:
                    grouped_dict[tag.name].append(entry)
    return grouped_dict


def get_free_tag_name(original_string, list):
    if original_string in list:
        counter = 1
        new_string = f"{original_string}_{counter}"
        while new_string in list:
            counter += 1
            new_string = f"{original_string}_{counter}"
        return new_string
    else:
        return original_string


@sly.handle_exceptions
def main():
    api = sly.Api.from_env()
    project_id = sly.env.project_id(raise_not_found=False)
    dataset_id = sly.env.dataset_id(raise_not_found=False)
    # The app is launched from dataset
    if project_id is None:
        dataset_info = api.dataset.get_info_by_id(dataset_id)
        project_id = dataset_info.project_id
        datasets = [dataset_info]
    else:
        project = api.project.get_info_by_id(project_id)
        datasets = api.dataset.get_list(project.id)

    # Add tag meta and check if tag with given name already exists
    project_meta = sly.ProjectMeta.from_json(api.project.get_meta(project_id))
    tag_meta_names = [tag_m.name for tag_m in project_meta.tag_metas]
    tag_name = get_free_tag_name("group_id", tag_meta_names)

    # Add and update tag meta
    tag_meta_group = sly.TagMeta(name=tag_name, value_type=sly.TagValueType.ANY_STRING)
    api.project.update_meta(project_id, project_meta.add_tag_meta(tag_meta_group))

    # Enable multi-tag mode and grouping
    api.project.update_settings(project_id, settings={"allowDuplicateTags": True})
    api.project.images_grouping(project_id, enable=True, tag_name=tag_name)
    sly.logger.info(
        f"Successfully updated project's settings, and enabled images grouping by the tag {tag_name}"
    )
    anns_dict = {}

    # Get list of datasets and iterate over it
    for dataset in datasets:
        # Get list of all the images and their ids in a dataset
        images = api.image.get_list(dataset.id)
        image_ids = [img.id for img in images]
        group_index = 0
        # Download all image annotations
        anns_json = api.annotation.download_json_batch(dataset_id=dataset.id, image_ids=image_ids)
        anns = [sly.Annotation.from_json(ann_json, project_meta) for ann_json in anns_json]
        sly.logger.info(f"Annotations of {len(anns)} images are successfully downloaded")
        # Generate and iterate over map, and add a tag to each image with their group id
        map = get_grouped_dict(image_ids, anns)
        for group_name, group_data in map.items():
            for i, (image_id, ann) in enumerate(group_data):
                if i % batch_size == 0:
                    group_index += 1
                tag = sly.Tag(tag_meta_group, f"{group_name}_{group_index}")

                if image_id in anns_dict:
                    ann = anns_dict[image_id]
                anns_dict[image_id] = ann.add_tag(tag)

    sly.logger.info(f"{len(anns_dict.values())} annotations is prepared to upload")
    image_ids_list = list(anns_dict.keys())
    annotations_list = list(anns_dict.values())

    # Upload the updated annotations in batches
    for batched_ids, batched_anns in zip(
        sly.batched(image_ids_list), sly.batched(annotations_list)
    ):
        api.annotation.upload_anns(batched_ids, batched_anns)
        sly.logger.info(f"Batch of {len(batched_anns)} was uploaded")


if __name__ == "__main__":
    main()
