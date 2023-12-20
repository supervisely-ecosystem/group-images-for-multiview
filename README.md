<div align="center" markdown>
<img src="https://github.com/supervisely-ecosystem/group-images-for-multiview/assets/115161827/34793345-0133-4d1e-b1fb-15de999c85f0"/>  

# Group Images for Multiview Labeling

<p align="center">
  <a href="#Overview">Overview</a> •
  <a href="#How-To-Run">How To Run</a> 
</p>

[![](https://img.shields.io/badge/supervisely-ecosystem-brightgreen)](https://ecosystem.supervise.ly/apps/supervisely-ecosystem/group-images-for-multiview)
[![](https://img.shields.io/badge/slack-chat-green.svg?logo=slack)](https://supervise.ly/slack)
![GitHub release (latest SemVer)](https://img.shields.io/github/v/release/supervisely-ecosystem/group-images-for-multiview)
[![views](https://app.supervise.ly/img/badges/views/supervisely-ecosystem/group-images-for-multiview)](https://supervise.ly)
[![runs](https://app.supervise.ly/img/badges/runs/supervisely-ecosystem/group-images-for-multiview)](https://supervise.ly)

</div>

# Overview

The application splits dataset's images into groups, adds grouping tags and enables multiview. Size of groups is determined my the **Batch size** slider in the application window. Also, three grouping options are available: *Group by Batches*, *Group by Image Tags* and *Group by Object Class*.

**Group by Batches**: splits the images into groups on a random basis. Affects every image.

**Group by Image Tags**: splits the images into groups based on their tags. Does not affect images, which have no tags.

**Group by Object Class**: splits the images into groups based on object's classes present on them. Does not affect images, with no objects on them.

Before running the app, be aware that this app changes the project it is applied to. It is recommended to make a copy of the project if you are afraid that the changes will have a negative impact.

# How to Run

1. Go to your Workspace

2. Right click to the project or dataset and run app from context menu

<img src="xxx">

