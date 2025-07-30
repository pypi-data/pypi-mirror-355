import numpy as np
import pandas as pd
import sqlalchemy


def construct_lightcurves(
    db_engine: sqlalchemy.engine.base.Engine, attribute: str = "int_flux"
):
    """Reconstruct a dataframe with lightcurves from the source relations defined in the standard database.

    Parameters
    ----------
    db_engine
        A sqlalchemy database engine.
    attribute: str
        The name of the attribute to use as value for the lightcurve.
        This can be any column name of the extraced_sources table.

    Returns
    -------
    A pandas DataFrame where each row is a lightcurve and each column is correlated to each image.
    """
    with db_engine.connect() as conn:
        query = "SELECT * FROM extracted_sources"
        sources = pd.read_sql_query(query, conn)

    lightcurves = pd.DataFrame(
        {
            "id": [],
        }
    ).set_index("id")
    total_nr_sources = sources.src_id.max() + 1
    for im_id in range(sources.im_id.max() + 1):
        fluxes = np.full(total_nr_sources, np.nan)
        im_slice = sources[sources.im_id == im_id]
        fluxes[im_slice.src_id.values] = im_slice[attribute].values
        lightcurves[f"im_{im_id}"] = fluxes
        # Update duplicate's history
        duplicate_slice = im_slice[im_slice.is_duplicate.astype("bool")]
        to_copy_slice = sources.loc[duplicate_slice["parent"]]
        lightcurves.loc[duplicate_slice["src_id"], lightcurves.columns[:-1]] = (
            lightcurves.loc[to_copy_slice["src_id"], lightcurves.columns[:-1]].values
        )

    return lightcurves


def construct_varmetric(db_engine: sqlalchemy.engine.base.Engine) -> pd.DataFrame:
    r"""Calculate lightcurve properties which can be used for filtering and isolating potential transients.

    The properties are based on the extracted_sources table.
    These properties are:
        - newsource
            Reference to the id of the first extracted source in the lightcurve.
        - v_int
            The flux coefficient of variation (V_ν), based on the integrated flux values.
        - eta_int
            The ‘reduced chi-squared’ variability index (η_ν), based on the integrated flux values.
        - sigma_rms_min
            Integrated flux from the from the extracted source that triggered an new source entry, divided by the minimum value of the estimated-RMS-map within the source-extraction region.
        - sigma_rms_max
            Integrated flux from the from the extracted source that triggered an new source entry, divided by the maximum value of the estimated-RMS-map within the source-extraction region.
        - lightcurve_max
            The maximum flux value of the lightcurve based on the integrated flux.
        - lightcurve_avg
            The average flux value of the lightcurve based on the integrated flux.
        - lightcurve_median
            The median flux value of the lightcurve based on the integrated flux.

    Parameters
    ----------
    db_engine
        A sqlalchemy database engine.

    Returns
    -------
    dict
        A dictionary with the lightcurve properties mentioned above.
    """
    with db_engine.connect() as conn:
        sources = pd.read_sql_query("SELECT * FROM extracted_sources", conn)
        images = pd.read_sql_query("SELECT * FROM images", conn)

    src_ids = np.unique(sources.src_id)
    first_extracted_source_id = np.zeros(len(src_ids), dtype=int)
    sigma_rms_min = np.zeros(len(src_ids), dtype=float)
    sigma_rms_max = np.zeros(len(src_ids), dtype=float)
    for src_id in src_ids:
        # Get the first image for the lightcurve in question.
        im_id = sources[sources.src_id == src_id].im_id.min()
        im = images.loc[im_id]

        src = sources.loc[(sources["src_id"] == src_id) & (sources["im_id"] == im_id)]
        first_extracted_source_id[src_id] = src.id
        sigma_rms_min[src_id] = src.int_flux / im.rms_min
        sigma_rms_max[src_id] = src.int_flux / im.rms_max

    # FIXME: split construct_lightcurves into a construct_lightcurves(db_engine) and
    #        a _construct_lightcurves(sources, images)

    lightcurves_int = construct_lightcurves(db_engine, attribute="int_flux")
    lightcurve_integrated_flux = lightcurves_int.to_numpy()
    lightcurves_int_err = construct_lightcurves(db_engine, attribute="int_flux_err")
    lightcurve_integrated_flux_error = lightcurves_int_err.to_numpy()

    nr_images_per_source = np.isfinite(lightcurve_integrated_flux).sum(axis=1)
    multiple_sources_mask = nr_images_per_source > 1
    lightcurve_integrated_flux = lightcurve_integrated_flux[multiple_sources_mask]
    lightcurve_integrated_flux_error = lightcurve_integrated_flux_error[
        multiple_sources_mask
    ]
    nr_images_per_source_masked = nr_images_per_source[multiple_sources_mask]

    integrated_flux_mean = (
        np.nansum(lightcurve_integrated_flux, axis=1) / nr_images_per_source_masked
    )
    integrated_flux_mean_sq = (
        np.nansum(lightcurve_integrated_flux**2, axis=1) / nr_images_per_source_masked
    )
    integrated_flux_mean_weighted = (
        np.nansum(
            lightcurve_integrated_flux / lightcurve_integrated_flux_error**2, axis=1
        )
        / nr_images_per_source_masked
    )
    integrated_flux_mean_weighted_sq = (
        np.nansum(
            lightcurve_integrated_flux**2 / lightcurve_integrated_flux_error**2, axis=1
        )
        / nr_images_per_source_masked
    )
    normalized_integrated_flux_weighted = (
        np.nansum(1.0 / lightcurve_integrated_flux_error**2, axis=1)
        / nr_images_per_source_masked
    )

    v_int = np.full(len(src_ids), np.nan)
    v_int[multiple_sources_mask] = (
        np.sqrt(
            nr_images_per_source_masked
            * (integrated_flux_mean_sq - integrated_flux_mean**2)
            / (nr_images_per_source_masked - 1.0)
        )
        / integrated_flux_mean
    )
    eta = np.full(len(src_ids), np.nan)
    eta[multiple_sources_mask] = (
        nr_images_per_source_masked
        * (
            integrated_flux_mean_weighted_sq
            - integrated_flux_mean_weighted**2 / normalized_integrated_flux_weighted
        )
        / (nr_images_per_source_masked - 1.0)
    )

    # Varmetric caluclations based on: https://github.com/transientskp/tkp/blob/b34582712b82b888a5a7b51b3ee371e682b8c349/tkp/testutil/db_subs.py#L188
    varmetric = pd.DataFrame(
        {
            "newsource": first_extracted_source_id,
            "v_int": v_int,
            "eta_int": eta,
            "sigma_rms_min": sigma_rms_min,
            "sigma_rms_max": sigma_rms_max,
        }
    )
    # The following are added separately such that the gaps are filled with nans and the lengths match the rest
    varmetric["lightcurve_max"] = np.nan
    varmetric["lightcurve_avg"] = np.nan
    varmetric["lightcurve_median"] = np.nan
    varmetric.loc[multiple_sources_mask, "lightcurve_max"] = np.max(
        lightcurve_integrated_flux, axis=1
    )
    varmetric.loc[multiple_sources_mask, "lightcurve_avg"] = np.mean(
        lightcurve_integrated_flux, axis=1
    )
    varmetric.loc[multiple_sources_mask, "lightcurve_median"] = np.median(
        lightcurve_integrated_flux, axis=1
    )

    return varmetric
