# Maintainer notes

Internal conventions for adding and updating parts. Not for users.

## Source of truth

The editable design CAD for released parts lives on a local CAD release drive. 
This repo holds **exports only** — both STEP and STL for every part. Always regenerate lost parts from the drive copy. 

## Adding a part

1. Put the master CAD in `CAD_Releases/<MODEL>/` on the drive.
2. Create `<model>/<part-name>/` here (kebab-case, e.g. `a3/gripper-attachment-points/`).
   Copy `_template/README.md` in and fill it out.
3. Export STEP and STL into the folder. Name files after the folder:
   `gripper-attachment-points.step`, `gripper-attachment-points.stl`.
4. Check print settings.
5. Add a photo or render to `images/`.
6. List the part in the model folder's README table.

## Revising a part

- Bump the `Rev` line in the part README and add a line to its changelog.
- Old revisions aren't kept in-tree — git history and release archives cover that.

## Releases

Tag a release when a part is added or revised: tag `vYYYY.MM.DD`, with a note
per changed part. Attach a zip per model (`a3-printables.zip`, …) so users can
grab everything at once.
