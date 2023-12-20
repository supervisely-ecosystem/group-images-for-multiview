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

sly.logger.debug(f"grouping_mode:{grouping_mode}, batch_size:{batch_size}")

tag_name = "group id"
tag_meta_group = sly.TagMeta(name=tag_name, value_type=sly.TagValueType.ANY_STRING)


def get_grouped_dict(anns, image_ids):
    if grouping_mode == "by-batches":
        return {"group": anns}  # спросить у гпт
    grouped_dict = defaultdict(list)

    # def get_attribute(ann):
    #     if grouping_mode == "obj-class":
    #         return ann.labels, "obj_class.name"
    #     elif grouping_mode == "tags":
    #         return ann.img_tags, "name"

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
        # attribute, attribute2 = get_attribute(ann)  # todo x-y
        # if attribute is not None:
        #     for x in attribute:
        #         y = attribute2.split(".")
        #         if len(y) > 1:
        #             key = getattr(getattr(x, y[0]), y[1])
        #         else:
        #             key = getattr(x, attribute2)
        #         entry = (image_id, ann)
        #         if entry not in grouped_dict[key]:
        #             grouped_dict[key].append(entry)

    return grouped_dict


@sly.handle_exceptions
def main():
    api = sly.Api.from_env()
    project_id = sly.env.project_id(raise_not_found=False)
    dataset_id = sly.env.dataset_id(raise_not_found=False)
    # print(dataset_id)
    # the app is launched from dataset
    if project_id is None:
        dataset_info = api.dataset.get_info_by_id(dataset_id)
        project_id = dataset_info.project_id
        datasets = [dataset_info]
    else:
        project = api.project.get_info_by_id(project_id)
        datasets = api.dataset.get_list(project.id)

    # if project is None:
    # raise KeyError(f"Project with ID {project_id} not found in your account")

    # Add tag meta
    meta = sly.ProjectMeta.from_json(api.project.get_meta(project_id))
    tag_meta = meta.get_tag_meta(tag_name)
    if tag_meta is None:
        meta = meta.add_tag_meta(tag_meta_group)
        api.project.update_meta(project_id, meta)

    # Enable multi-tag mode and grouping
    api.project.update_settings(project_id, settings={"allowDuplicateTags": True})
    api.project.images_grouping(project_id, enable=True, tag_name=tag_name)
    anns_dict = {}

    # Get list of datasets and iterate over it
    for dataset in datasets:
        # Get list of all the images and their ids in a dataset
        images = api.image.get_list(dataset.id)
        image_ids = [img.id for img in images]
        group_index = 0
        # Download all image annotations
        anns_json = api.annotation.download_json_batch(dataset_id=dataset.id, image_ids=image_ids)
        anns = [sly.Annotation.from_json(ann_json, meta) for ann_json in anns_json]
        # Iterate over annotations, and add a tag to each image  with their group id

        map = get_grouped_dict(
            anns,
            image_ids,
        )
        # ann_list = []
        for group_name, group_data in map.items():
            for i, (image_id, ann) in enumerate(group_data):
                if i % batch_size == 0:
                    group_index += 1
                tag = sly.Tag(tag_meta_group, f"{group_name}_{group_index}")

                # ann = ann.add_tag(tag)
                if image_id in anns_dict:
                    ann = anns_dict[image_id]
                anns_dict[image_id] = ann.add_tag(tag)

    # Upload the updated annotations
    sly.logger.info(f"{len(anns_dict.values())} annotations is prepared to upload")
    image_ids_list = list(anns_dict.keys())
    annotations_list = list(anns_dict.values())

    for batched_ids, batched_anns in zip(
        sly.batched(image_ids_list), sly.batched(annotations_list)
    ):
        api.annotation.upload_anns(batched_ids, batched_anns)
        sly.logger.info(f"Batch of {len(batched_anns)} was uploaded")


if __name__ == "__main__":
    main()
