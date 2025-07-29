"""Algorithm for establishing number of results that match a given criteria."""

from __future__ import annotations

from datetime import datetime
import hashlib
from typing import TYPE_CHECKING, Any, Mapping, Optional

import pandas as pd

from bitfount.externals.ehr.nextgen.api import NextGenEnterpriseAPI
from bitfount.externals.ehr.nextgen.types import PatientCodeStatus
from bitfount.federated.algorithms.ophthalmology.ga_trial_inclusion_criteria_match_algorithm_base import (  # noqa: E501
    BaseGATrialInclusionAlgorithmFactorySingleEye,
    BaseGATrialInclusionWorkerAlgorithmSingleEye,
)
from bitfount.federated.algorithms.ophthalmology.ophth_algo_types import (
    AGE_COL,
    CNV_THRESHOLD,
    FILTER_FAILED_REASON_COLUMN,
    FILTER_MATCHING_COLUMN,
    ICD10_PREFIX,
    LARGEST_GA_LESION_LOWER_BOUND,
    MAX_CNV_PROBABILITY_COL_PREFIX,
    NAME_COL,
    PREV_APPOINTMENTS_COL,
    TOTAL_GA_AREA_COL_PREFIX,
    TOTAL_GA_AREA_LOWER_BOUND,
    TOTAL_GA_AREA_UPPER_BOUND,
    ColumnFilter,
)
from bitfount.federated.algorithms.ophthalmology.ophth_algo_utils import (
    _add_filtering_to_df,
)
from bitfount.federated.logging import _get_federated_logger

if TYPE_CHECKING:
    pass


# Constrain on age of patient
# Allow for patients about to turn 50 in the next year
PATIENT_AGE_LOWER_BOUND_CHARCOAL = 50 - 1

# Constraint on minimum number of years of history
# Allow for patients with 1 fewer year of history
YEARS_OF_APPOINTMENT_HISTORY = 3 - 1

# ICD 10 Codes specific for this project
ICD10CODES = {
    "H35.3112",  # Right: Intermediate Dry Stage
    "H35.3113",  # Right: Advanced Atrophic w/o Subfoveal Involvement
    "H35.3114",  # Right: Advanced Atrophic w/ Subfoveal Involvement
    "H35.3122",  # Left: Intermediate Dry Stage
    "H35.3123",  # Left: Advance Atrophic w/o Subfoveal Involvement
    "H35.3124",  # Left: Advance Atrophic w/ Subfoveal Involvement
    "H35.3132",  # BiLateral: Intermediate Dry Stage
    "H35.3133",  # BiLateral: Advance Atrophic w/o Subfoveal Involvement
    "H35.3134",  # BiLateral: Advance Atrophic w/ Subfoveal Involvement
}

logger = _get_federated_logger("bitfount.federated")

# This algorithm is designed to find patients that match a set of clinical criteria.
# The criteria are as follows:
# 1. Has diagnosis of Dry AMD OR Total GA area greater than TOTAL_GA_AREA_LOWER_BOUND
# 2. No CNV (CNV probability less than CNV_THRESHOLD)
# 3. Age greater than PATIENT_AGE_LOWER_BOUND_CHARCOAL
# 4. Appointment history going back at least YEARS_OF_APPOINTMENT_HISTORY years


class _WorkerSide(BaseGATrialInclusionWorkerAlgorithmSingleEye):
    """Worker side of the algorithm."""

    def __init__(
        self,
        *,
        cnv_threshold: float = CNV_THRESHOLD,
        largest_ga_lesion_lower_bound: float = LARGEST_GA_LESION_LOWER_BOUND,
        largest_ga_lesion_upper_bound: Optional[float] = None,
        total_ga_area_lower_bound: float = TOTAL_GA_AREA_LOWER_BOUND,
        total_ga_area_upper_bound: float = TOTAL_GA_AREA_UPPER_BOUND,
        patient_age_lower_bound: Optional[int] = None,
        patient_age_upper_bound: Optional[int] = None,
        renamed_columns: Optional[Mapping[str, str]] = None,
        **kwargs: Any,
    ) -> None:
        if patient_age_upper_bound is not None:
            logger.warning(
                f"Charcoal algorithm explicitly sets patient_age_lower_bound;"
                f" received value of {patient_age_lower_bound}."
                f" Using {PATIENT_AGE_LOWER_BOUND_CHARCOAL} instead."
            )
        super().__init__(
            cnv_threshold=cnv_threshold,
            largest_ga_lesion_lower_bound=largest_ga_lesion_lower_bound,  # not used
            largest_ga_lesion_upper_bound=largest_ga_lesion_upper_bound,  # not used
            total_ga_area_lower_bound=total_ga_area_lower_bound,
            total_ga_area_upper_bound=total_ga_area_upper_bound,  # not used
            # Explicitly overriden
            patient_age_lower_bound=PATIENT_AGE_LOWER_BOUND_CHARCOAL,
            patient_age_upper_bound=patient_age_upper_bound,
            renamed_columns=renamed_columns,
            **kwargs,
        )

    # Note: The following method was renamed from run() as it returns a dataframe
    #     and hence has a different signature from the parent class
    def run_and_return_dataframe(
        self,
        dataframe: pd.DataFrame,
    ) -> pd.DataFrame:
        """Finds number of patients that match the clinical criteria.

        Args:
            dataframe: The dataframe to process.

        Returns:
            A tuple of counts of patients that match the clinical criteria.
            Tuple is of form (match criteria, don't match criteria).
        """
        if dataframe.empty:
            return dataframe

        dataframe = self._add_age_col(dataframe)
        dataframe = self._filter_by_criteria(dataframe)

        return dataframe

    def get_column_filters(self) -> list[ColumnFilter]:
        """Returns the column filters for the algorithm.

        Returns a list of ColumnFilter objects that specify the filters for the
        columns that the algorithm is interested in. This is used to filter other
        algorithms using the same filters.
        """
        total_ga_area_column = self._get_column_name(TOTAL_GA_AREA_COL_PREFIX)
        max_cnv_column = self._get_column_name(MAX_CNV_PROBABILITY_COL_PREFIX)

        # Note: We are not using self.get_base_column_filters here as it contains
        #     filters not required for charcoal

        # There is a missing column filter here which does not fit in this framework:
        #  - Patient EITHER has a diagnosis code OR has GA detected in scan
        return [
            ColumnFilter(
                column=max_cnv_column,
                operator="<=",
                value=self.cnv_threshold,
            ),
            ColumnFilter(
                column=total_ga_area_column,
                operator=">=",
                value=self.total_ga_area_lower_bound,
            ),
            ColumnFilter(
                column=AGE_COL,
                operator=">=",
                value=PATIENT_AGE_LOWER_BOUND_CHARCOAL,
            ),
        ]

    def _add_exclusion_reasons_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        # In the future, we may want to reimplement _add_filtering_to_df for Charcoal
        #    as it adds a FILTER_MATCHING_COLUMN which we do not need and will
        #    overwrite later on
        if FILTER_FAILED_REASON_COLUMN not in df:
            df[FILTER_FAILED_REASON_COLUMN] = ""
        for col_filter in self.get_column_filters():
            if col_filter.column in df.columns:
                df = _add_filtering_to_df(df, col_filter)
        df[FILTER_FAILED_REASON_COLUMN] = df[FILTER_FAILED_REASON_COLUMN].apply(
            lambda x: x.strip(", ")
        )
        return df

    def _filter_by_criteria(self, df: pd.DataFrame) -> pd.DataFrame:
        df = self._add_exclusion_reasons_columns(df)

        # Establish which rows fit all the criteria
        eligibility_list: list[bool] = []
        for _idx, row in df.iterrows():
            patient_name: str = str(row[NAME_COL])
            patient_name_hash: str = hashlib.md5(patient_name.encode()).hexdigest()  # nosec[blacklist] # Reason: this is not a security use case

            # Age criterion
            if not row[AGE_COL] >= self.patient_age_lower_bound:
                logger.debug(f"Patient {patient_name_hash} excluded due to age")
                eligibility_list.append(False)
                continue

            # Exclude if eye has Wet AMD
            cnv_entry = row[MAX_CNV_PROBABILITY_COL_PREFIX]
            if cnv_entry >= self.cnv_threshold:
                logger.debug(
                    f"Patient {patient_name_hash} excluded due to CNV in the "
                    f"current eye"
                )
                eligibility_list.append(False)
                continue

            # Dry AMD Condition criterion (either via diagnosis or detected in scan)
            if not any(
                row.get(f"{ICD10_PREFIX}{code}")
                in (PatientCodeStatus.PRESENT, PatientCodeStatus.PRESENT.value)
                for code in ICD10CODES
            ):
                ga_area_entry = row[TOTAL_GA_AREA_COL_PREFIX]
                if ga_area_entry < self.total_ga_area_lower_bound:
                    logger.debug(
                        f"Patient {patient_name_hash} excluded due to no "
                        f"current diagnosis for macular degeneration"
                    )
                    eligibility_list.append(False)
                    continue
                else:
                    # Note: Patient will still be included if model failed to
                    #    generate a total ga area prediction (value is nan)
                    logger.info(
                        f"Patient {patient_name_hash} may have GA"
                        f" detected in scan: {ga_area_entry}"
                    )
            else:
                logger.debug(
                    f"Patient {patient_name_hash} has "
                    f"current diagnosis for macular degeneration"
                )

            # Check for 3-years history of appointment history
            appointment_dates = [
                datetime.strptime(
                    appt.get("appointmentDate"),
                    NextGenEnterpriseAPI.DATETIME_STR_FORMAT,
                )
                for appt in row[PREV_APPOINTMENTS_COL]
            ]
            if appointment_dates:
                days_since_first_appointment = (
                    datetime.today() - min(appointment_dates)
                ).days
                if days_since_first_appointment <= 365 * YEARS_OF_APPOINTMENT_HISTORY:
                    logger.debug(
                        f"Patient {patient_name_hash} excluded due to not "
                        f"having long enough history of macular degeneration "
                        f"({days_since_first_appointment} days)"
                    )
                    eligibility_list.append(False)
                    continue

            # If we reach here, all criteria have been matched
            logger.debug(f"Patient {patient_name_hash} included: matches all criteria")
            eligibility_list.append(True)

        # Add column to dataframe
        df[FILTER_MATCHING_COLUMN] = eligibility_list

        return df


class TrialInclusionCriteriaMatchAlgorithmCharcoal(
    BaseGATrialInclusionAlgorithmFactorySingleEye
):
    """Algorithm for establishing number of patients that match clinical criteria."""

    def worker(self, **kwargs: Any) -> _WorkerSide:
        """Worker-side of the algorithm."""
        return _WorkerSide(
            cnv_threshold=self.cnv_threshold,
            largest_ga_lesion_lower_bound=self.largest_ga_lesion_lower_bound,
            largest_ga_lesion_upper_bound=self.largest_ga_lesion_upper_bound,
            total_ga_area_lower_bound=self.total_ga_area_lower_bound,
            total_ga_area_upper_bound=self.total_ga_area_upper_bound,
            patient_age_lower_bound=self.patient_age_lower_bound,
            patient_age_upper_bound=self.patient_age_upper_bound,
            **kwargs,
        )
