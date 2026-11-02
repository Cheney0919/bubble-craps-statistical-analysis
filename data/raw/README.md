# Raw data

Put the source roll logs here: `roll_log_A.csv`, plus `roll_log_B.csv` if the fallback machine was used. These are the files read by the analysis pipeline. Columns are defined in [`../../docs/data_dictionary.md`](../../docs/data_dictionary.md). Because the course requires raw data, they are committed once collection is complete. The log must contain no names, faces, financial details, or other personal information.

If reconciliation requires a documented correction, preserve a byte-for-byte original export separately as `roll_log_A_original_export.csv` (and likewise for B, if applicable). Record the correction with flag `C`, a note naming its verification source, and an entry in `docs/deviations.md`.

For this completed study, `roll_log_A_original_export.csv` is the byte-for-byte initial export. `roll_log_A.csv` is the reconciled log used by the scripts; its one video-confirmed correction is flagged `C`, explained in its note, and documented in [`../../docs/deviations.md`](../../docs/deviations.md).


