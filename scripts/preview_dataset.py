import pandas as pd

p = 'fraud_dataset-1.csv'
print('Loading:', p)
df = pd.read_csv(p)
print('Shape:', df.shape)
print('\nMissing per column:')
print(df.isnull().sum())
print('\nColumns:')
print(list(df.columns))
if 'Is_Fraud' in df.columns:
    print('\nTarget value counts:')
    print(df['Is_Fraud'].value_counts(dropna=False))
    print('\nTarget distribution:')
    print(df['Is_Fraud'].value_counts(normalize=True, dropna=False))
else:
    print('\nWarning: target column `Is_Fraud` not found. Available columns:')
    print(list(df.columns))

print('\nSample rows:')
print(df.head(10).to_string(index=False))
