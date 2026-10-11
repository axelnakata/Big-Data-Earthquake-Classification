"""Shared setup for notebooks: env for Hadoop, shell helper, Spark session, HDFS paths."""
import getpass, os, subprocess, sys, time

# Spark's Python workers must use the same interpreter as the notebook (.venv 3.11), not the system python3 (3.9).
os.environ['PYSPARK_PYTHON'] = os.environ['PYSPARK_DRIVER_PYTHON'] = sys.executable
# Bind Spark (driver + UI :4040) to localhost only, not the Wi-Fi/LAN address.
os.environ['SPARK_LOCAL_IP'] = '127.0.0.1'

# All seismic times are UTC. Without this, Spark→Python converts timestamps to the Mac's local time (WIB, +7h).
os.environ['TZ'] = 'UTC'; time.tzset()

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_TABLES = os.path.join(ROOT, 'outputs', 'tables')
OUT_FIGS = os.path.join(ROOT, 'outputs', 'figures')
HDFS = 'hdfs://localhost:9000'
RAW, PROCESSED, QUALITY = '/datalake/raw', '/datalake/processed', '/datalake/quality'
DATASETS = ['comcat', 'exotic', 'noise']
CLASSES = ['earthquake', 'explosion', 'surface_event', 'noise']
COLORS = {'earthquake': '#1f77b4', 'explosion': '#d62728', 'surface_event': '#2ca02c', 'noise': '#7f7f7f'}
ML = '/datalake/ml'

os.environ['JAVA_HOME'] = subprocess.check_output(['/usr/libexec/java_home', '-v', '11']).decode().strip()
os.environ['HADOOP_HOME'] = os.path.expanduser('~/opt/hadoop')
os.environ['PATH'] = os.environ['HADOOP_HOME'] + '/bin:' + os.environ['PATH']
# Spark's bundled Hadoop client must read OUR hdfs-site.xml, otherwise it writes with its default dfs.replication=3.
os.environ['HADOOP_CONF_DIR'] = os.environ['HADOOP_HOME'] + '/etc/hadoop'
os.environ['HADOOP_ROOT_LOGGER'] = 'ERROR,console'  # hide the harmless native-library warning


def sh(cmd, check=True, quiet=False):
    """Run a shell command, print it and its output (so the notebook shows the evidence)."""
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    out = (r.stdout + r.stderr).strip()
    if not quiet:
        print('$', cmd); print(out)
    if check and r.returncode != 0:
        raise RuntimeError(f'command failed ({r.returncode}): {cmd}')
    return out


def spark_session(app='pnwml', driver_mem='12g', packages=None):
    from pyspark.sql import SparkSession
    builder = SparkSession.builder
    if packages:
        builder = builder.config('spark.jars.packages', packages)
    spark = (builder.master('local[*]').appName(app)
             .config('spark.driver.memory', driver_mem)  # ~50% of 24 GB RAM
             .config('spark.local.dir', os.path.expanduser('~/pnwml-data/tmp/spark-local'))
             .config('spark.hadoop.fs.defaultFS', HDFS)
             .config('spark.sql.session.timeZone', 'UTC')
             .config('spark.driver.extraJavaOptions', '-Duser.timezone=UTC')
             .getOrCreate())
    spark.sparkContext.setLogLevel('ERROR')
    return spark


def webhdfs():
    import fsspec
    return fsspec.filesystem('webhdfs', host='localhost', port=9870, user=getpass.getuser())


def save_md(df, name, title=None, note=None):
    """Write a pandas DataFrame to outputs/tables/<name>.md (for pasting into the report)."""
    os.makedirs(OUT_TABLES, exist_ok=True)
    body = (f'# {title}\n\n' if title else '') + (f'{note}\n\n' if note else '') + df.to_markdown(index=False) + '\n'
    with open(os.path.join(OUT_TABLES, f'{name}.md'), 'w') as f:
        f.write(body)
    return os.path.join(OUT_TABLES, f'{name}.md')


def save_fig(name):
    """Save the current matplotlib figure to outputs/figures/<name>.png."""
    import matplotlib.pyplot as plt
    os.makedirs(OUT_FIGS, exist_ok=True)
    plt.savefig(os.path.join(OUT_FIGS, f'{name}.png'), dpi=150, bbox_inches='tight')
