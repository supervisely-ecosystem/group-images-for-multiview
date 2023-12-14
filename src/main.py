import os
from dotenv import load_dotenv
import supervisely as sly

# load ENV variables for debug
# has no effect in production
if sly.is_development:
    load_dotenv(os.path.expanduser("~/supervisely.env"))
    load_dotenv("local.env")

grouping_type = os.environ["modal.state.selectOption"]
batch_size = int(os.environ["modal.state.sliderValue"])

tag_name = "group id"
tag_meta_group = sly.TagMeta(name=tag_name, value_type=sly.TagValueType.ANY_NUMBER)

def main():
    api = sly.Api.from_env()
    project_id = sly.env.project_id()
    project = api.project.get_info_by_id(project_id)
    if project is None:
        raise KeyError(f"Project with ID {project_id} not found in your account")
    
    # Add tag meta
    meta = sly.ProjectMeta.from_json(api.project.get_meta(project_id))
    tag_meta = sly.ProjectMeta.get_tag_meta(meta, tag_name)
    if tag_meta is None:
        sly.ProjectMeta.add_tag_meta(tag_meta_group)
        api.project.update_meta(project_id, meta.to_json())

    # Enable multi-tag mode and grouping
    api.project.update_settings(project_id, settings={"allowDuplicateTags": True})
    api.project.images_grouping(project_id, enable=True, tag_name=tag_name)

    # Get list of datasets and iterate over it
    datasets = api.dataset.get_list(project.id)
    for dataset in datasets:
        # Get list of all the images and their ids in a dataset
        images = api.image.get_list(dataset.id)
        image_ids = [img.id for img in images]
        # Download all image annotations
        anns_json = api.annotation.download_json_batch(dataset_id=dataset.id, image_ids=image_ids)
        anns = [sly.Annotation.from_json(ann_json, meta) for ann_json in anns_json]
        # Iterate over annotations, and add a tag to each image  with their group id
        ann_list = []
        for i, ann in enumerate(anns):
            value = 1
            if i % batch_size:
                value = value + 1
            tag = sly.Tag(tag_meta_group, value)
            ann = ann.add_tag(tag=tag)
            ann_list.append(ann)
        # Upload the updated annotations
        api.annotation.upload_anns(image_ids, ann_list)

if __name__ == "__main__":
    main()
