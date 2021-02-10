from pyspark.context import SparkContext
from awsglue.context import GlueContext

from pyspark.sql.functions import col

INVALID_REVISION_REGEX = r'revert|undo|undid|robot'
NPOV_REGEX = (r'([- wnv\/\\\:\{\(\[\"\+\'\.\|\_\)\#\=\;\~](rm)'
              r'?(attribute)?(yes)?(de)?n?pov)|([- n\/\\\:\{\('
              r'\[\"\+\'\.\|\_\)\#\;\~]neutral)')

S3_PATH = 's3://mm-wikipedia-dump/nlwiki-20200901-stub-meta-history.xml'
N_ROW_LIMIT = None

glueContext = GlueContext(SparkContext.getOrCreate())
spark = glueContext.spark_session

if N_ROW_LIMIT:
    print('Loading {} rows...'.format(N_ROW_LIMIT))
    comment_data = \
        spark.read.format("com.databricks.spark.xml")\
        .options(rowTag='revision')\
        .load(S3_PATH)\
        .limit(N_ROW_LIMIT)
    print("Total number of comments: ", N_ROW_LIMIT)

else:
    print('Loading entire dataset...')
    comment_data = \
        spark.read.format("com.databricks.spark.xml")\
        .options(rowTag='revision')\
        .load(S3_PATH)
    print("Total number of comments: ", comment_data.count())

print('Partitions: ', comment_data.rdd.getNumPartitions())

comment_data = \
    comment_data.select(
        col('id').alias('revision_id'),
        col('comment._VALUE').alias('revision_comment')
    )

# Remove null comments
comment_data = \
    comment_data.where(
        col('revision_comment').isNotNull()
    )
print("Non-null comments: ", comment_data.count())

# Filter out invalid revisions
comment_data = \
    comment_data.filter(
        col('revision_comment').rlike(INVALID_REVISION_REGEX) == False
    )

print("Valid comments: ", comment_data.count())

# Filter out non-NPOV comments
comment_data = \
    comment_data.filter(
        col('revision_comment').rlike(NPOV_REGEX) == True
    )

print("NPOV comments: ", comment_data.count())

# Save data
WRITE_PATH = 's3a://mm-wikipedia-dump/npov_revisions_2'

print('Writing data to {}...'.format(WRITE_PATH))
comment_data.write.save(
    WRITE_PATH,
    format='csv',
    mode="overwrite",
    header=True)

print('Done!')
