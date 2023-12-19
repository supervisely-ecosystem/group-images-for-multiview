import os
from dotenv import load_dotenv
import supervisely as sly
from collections import defaultdict

# load ENV variables for debug
# has no effect in production
if sly.is_development:
    load_dotenv(os.path.expanduser("~/supervisely.env"))
    load_dotenv("local.env")

grouping_mode = os.environ["modal.state.selectOption"]
batch_size = int(os.environ["modal.state.sliderValue"])

tag_name = "group id"
tag_meta_group = sly.TagMeta(name=tag_name, value_type=sly.TagValueType.ANY_STRING)


def get_grouped_dict(anns, grouping_mode):
    grouped_dict = defaultdict(list)

    def get_attribute(ann):
        if grouping_mode == "obj-class":
            return ann.label.obj_class
        elif grouping_mode == "tags":
            return ann.img_tags
        else:
            return None

    for ann in anns:
        attribute = get_attribute(ann)
        if attribute is not None:
            grouped_dict[attribute.name].append(ann)
        else:
            grouped_dict["group"].append(ann)

    return grouped_dict


@sly.handle_exceptions
def main():
    api = sly.Api.from_env()
    project_id = sly.env.project_id()
    dataset_id = sly.env.dataset_id()
    dataset_info = api.dataset.get_info_by_id(dataset_id)

    if project_id is None:
        project_id = dataset_info.project_id
    project = api.project.get_info_by_id(project_id)
    if project is None:
        raise KeyError(f"Project with ID {project_id} not found in your account")

    # Add tag meta
    meta = sly.ProjectMeta.from_json(api.project.get_meta(project_id))
    tag_meta = meta.get_tag_meta(tag_name)  # todo address
    if tag_meta is None:
        meta = meta.add_tag_meta(tag_meta_group)
        api.project.update_meta(project_id, meta)

    # Enable multi-tag mode and grouping
    api.project.update_settings(project_id, settings={"allowDuplicateTags": True})
    api.project.images_grouping(project_id, enable=True, tag_name=tag_name)

    # Get list of datasets and iterate over it
    if dataset_id is None:
        datasets = api.dataset.get_list(project.id)
    else:
        datasets = [dataset_info]
    for dataset in datasets:
        # Get list of all the images and their ids in a dataset
        images = api.image.get_list(dataset.id)
        image_ids = [img.id for img in images]
        group_index = 0
        ann_list = []
        for ids in sly.batched(
            image_ids, batch_size * 10
        ):  # todo хуйня по батч сайзу какая-то, чесслово
            # Download all image annotations
            anns_json = api.annotation.download_json_batch(dataset_id=dataset.id, image_ids=ids)
            anns = [sly.Annotation.from_json(ann_json, meta) for ann_json in anns_json]
            # Iterate over annotations, and add a tag to each image  with their group id

            map = get_grouped_dict(anns, grouping_mode)

            for i, (k, v) in enumerate(map.items()):
                if i % batch_size == 0:
                    group_index += 1
                tag = sly.Tag(tag_meta_group, f"{k}_{group_index}")
                ann_list.extend([ann.add_tag(tag) for ann in v])

            # Upload the updated annotations
            api.annotation.upload_anns(ids, ann_list)


if __name__ == "__main__":
    main()
