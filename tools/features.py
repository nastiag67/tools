import pandas as pd
import numpy as np
from datetime import datetime

from sklearn.feature_selection import VarianceThreshold, RFE, SelectFromModel
from sklearn.ensemble import RandomForestClassifier, ExtraTreesClassifier
from sklearn.preprocessing import StandardScaler


class FeatureSelectionPipeline:
    """Assumes y - last column in df"""
    def __init__(self, df):
        self.df = df
        self.X = df.iloc[:, :-1]
        self.y = df.iloc[:, -1]

    def low_variance(self, threshold):
        """

        Parameters
        ----------
        threshold :
            

        Returns
        -------

        """
        # Normalize the data
        normalized_df = self.df / self.df.mean()

        # Create a VarianceThreshold feature selector
        sel = VarianceThreshold(threshold=threshold)

        # Fit the selector to normalized df
        # because higher values may have higher variances => need to adjust for that
        sel.fit(normalized_df)

        # Create a boolean mask: gives True/False value on if each feature’s Var > threshold
        mask = sel.get_support()

        # Apply the mask to create a reduced dataframe
        reduced_df = self.df.loc[:, mask]

        print(f"Dimensionality reduced from {self.df.shape[1]} to {reduced_df.shape[1]-1}.")
        return reduced_df

    def RFE_selection(self, n_features_to_select, step, mask=None):
        """

        Parameters
        ----------
        n_features_to_select :
            
        step :
            
        mask :
             (Default value = None)

        Returns
        -------

        """

        if mask is not None:
            # Apply the mask to the feature dataset X
            reduced_df = self.df.loc[:, mask]
            return reduced_df

        # DROP THE LEAST IMPORTANT FEATURES ONE BY ONE
        # Set the feature eliminator to remove 2 features on each step
        rfe = RFE(estimator=RandomForestClassifier(random_state=42),
                  n_features_to_select=n_features_to_select,
                  step=step,
                  verbose=0)

        # Fit the model to the training data
        rfe.fit(self.X, self.y)

        # Create a mask: remaining column names
        mask = rfe.support_

        # Apply the mask to the feature dataset X
        reduced_X = self.X.loc[:, mask]
        reduced_df = pd.concat([reduced_X, self.y], axis=1)

        print(f"Dimensionality reduced from {self.df.shape[1]} to {reduced_df.shape[1]-1}.")
        return reduced_df, mask

    def ensemble(self, models, n_features_to_select, mask=None):
        """

        Parameters
        ----------
        models :
            
        n_features_to_select :
            
        mask :
             (Default value = None)

        Returns
        -------

        """
        if mask is not None:
            # Apply the mask to the feature dataset X
            reduced_df = self.df.loc[:, mask]
            return reduced_df

        rfe_masks = []
        for modelname, model in zip(models.keys(), models.values()):
            print(f"RFE using the model: {modelname}")
            # Select n_features_to_selec with RFE on a GradientBoostingRegressor, drop 3 features on each step
            rfe_modelname = RFE(estimator=model, n_features_to_select=n_features_to_select, step=1, verbose=0)
            rfe_modelname.fit(self.X, self.y)

            # Assign the support array to gb_mask
            mask_modelname = rfe_modelname.support_
            rfe_masks.append(mask_modelname)

        # Sum the votes of the models
        n_models = len(rfe_masks)
        votes = np.sum(rfe_masks, axis=0)

        # Create a mask for features selected by all 2 models
        meta_mask = votes >= n_models

        # Apply the dimensionality reduction on X
        reduced_X = self.X.loc[:, meta_mask]
        reduced_df = pd.concat([reduced_X, self.y], axis=1)

        print(f"Dimensionality reduced from {self.df.shape[1]} to {reduced_df.shape[1]-1}.")
        return reduced_df, meta_mask

    def tree_based(self, threshold, mask=None):
        """

        Parameters
        ----------
        threshold :
            
        mask :
             (Default value = None)

        Returns
        -------

        """

        if mask is not None:
            # Apply the mask to the feature dataset X
            reduced_df = self.df.loc[:, mask]
            return reduced_df

        # Fit the random forest model to the training data
        rf = RandomForestClassifier(random_state=42)
        rf.fit(self.X, self.y)

        # Print the importances per feature
        # for unimportant features – almost 0
        # better than RFE, since the resulting values here r comparable bn features by default, cuz always sum to 1
        # => DON’T NEED TO SCALE THE DATA

        # Create a mask for features importances above the threshold
        mask = rf.feature_importances_ >= threshold

        # Apply the mask to the feature dataset X to implement the feature selection
        reduced_X = self.X.loc[:, mask]
        reduced_df = pd.concat([reduced_X, self.y], axis=1)
        # MUST BE CAREFUL WITH DROPPING SEVERAL FEATURES AT ONCE, BETTER DO IT ONE BY ONE USING RFE

        print(f"Dimensionality reduced from {self.df.shape[1]} to {reduced_df.shape[1]-1}.")
        return reduced_df, mask

    def extra_trees(self, st_scaler=True, mask=None):
        """

        Parameters
        ----------
        st_scaler :
             (Default value = True)
        mask :
             (Default value = None)

        Returns
        -------

        """

        if mask is not None:
            # Apply the mask to the feature dataset X
            reduced_df = self.df[mask]
            return reduced_df

        if st_scaler:
            # scaling
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(self.X)
        else:
            X_scaled = self.X

        # extract feature importances
        model = ExtraTreesClassifier(random_state=42)
        model.fit(X_scaled, self.y)
        importances = pd.DataFrame(model.feature_importances_)

        # Select only the features which have an importance bigger than the mean importance of the whole dataset
        sfm = SelectFromModel(model, threshold=importances.mean())
        sfm.fit(X_scaled, self.y)

        # Create a mask for features importances
        feature_idx = sfm.get_support()
        mask = self.X.columns[feature_idx]

        # Apply the mask to the feature dataset X to implement the feature selection
        reduced_X = self.X.loc[:, mask]
        reduced_df = pd.concat([reduced_X, self.y], axis=1)
        print(f"Dimensionality reduced from {self.df.shape[1]} to {reduced_df.shape[1]-1}.")

        return reduced_df, mask

    def L1(self):
        """ """
        pass


class FeatureEngineeringPipeline:
    """ """
    def __init__(self, df):
        self.df = df

    def normalization(self):
        """ """
        pass

    def standartization(self):
        """ """
        pass

    def _imputation(self, how):
        """how - one of the following:
            - average,
            - same value outside of normal range,
            - value from the middle of the range,
            - use the missing value as target for regression problem,
            - increase dimensionality by adding a binary indicator feature for each feature with missing values

        Parameters
        ----------
        how :
            

        Returns
        -------

        """

        pass

    def missing(self, remove=True, impute=False, learn=False):
        """

        Parameters
        ----------
        remove :
             (Default value = True)
        impute :
             (Default value = False)
        learn :
             (Default value = False)

        Returns
        -------

        """

        if impute:
            result = self._imputation(how='method')

        return result


    def normalization(self):
        """ """
        pass

