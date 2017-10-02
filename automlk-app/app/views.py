from app import app
import time
from flask import render_template, send_file, redirect, request, abort, flash
from werkzeug import secure_filename
from .helper import *
from .form import DatasetForm
from automlk.context import get_dataset_folder
from automlk.dataset import get_dataset_list, get_dataset
from automlk.search import get_search_rounds
from automlk.graphs import graph_history_search
from automlk.store import set_key_store
from automlk.dataset import create_dataset
from automlk.monitor import get_heart_beeps


@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
def index():
    # home page: list of models
    datasets = get_dataset_list(include_status=True)[::-1]
    return render_template('index.html', datasets=datasets, refresher=int(time.time()))


@app.route('/start/<string:dataset_id>', methods=['GET'])
def start(dataset_id):
    set_key_store('dataset:%s:status' % dataset_id, 'searching')
    return redirect('/index')


@app.route('/pause/<string:dataset_id>', methods=['GET'])
def pause(dataset_id):
    set_key_store('dataset:%s:status' % dataset_id, 'pause')
    return redirect('/index')


@app.route('/dataset/<string:dataset_id>', methods=['GET', 'POST'])
def dataset(dataset_id):
    # zoom on a specific dataset
    dataset = get_dataset(dataset_id)
    search = get_search_rounds(dataset.dataset_id)
    if len(search) > 0:
        best = get_best_models(search)
        # separate models (level 0) from ensembles (level 1)
        best1 = best[best.level == 1]
        best2 = best[best.level == 2]
        graph_history_search(dataset, search, best1, 1)
        graph_history_search(dataset, search, best2, 2)
        return render_template('dataset.html', dataset=dataset, best1=best1.to_dict(orient='records'),
                               best2=best2.to_dict(orient='records'),
                               n_searches1=len(search[search.level == 1]),
                               n_searches2=len(search[search.level == 2]),
                               refresher=int(time.time()))
    else:
        return render_template('dataset.html', dataset=dataset, n_searches1=0, refresher=int(time.time()))


# TODO: graph per parameter


@app.route('/details/<string:prm>', methods=['GET', 'POST'])
def details(prm):
    # list of searches for a specific type of model
    dataset_id, model = prm.split(';')
    dataset = get_dataset(dataset_id)
    search = get_search_rounds(dataset.dataset_id)
    cols, best = get_best_details(search, model)
    best = best.to_dict(orient='records')[:10]
    return render_template('details.html', dataset=dataset, model=model, best=best, cols=cols,
                           refresher=int(time.time()))


@app.route('/round/<string:prm>', methods=['GET', 'POST'])
def round(prm):
    # details of a search round (1 preprocessing + 1 model configuration)
    dataset_id, round_id = prm.split(';')
    dataset = get_dataset(dataset_id)
    search = get_search_rounds(dataset.dataset_id)
    round = search[search.round_id == int(round_id)].to_dict(orient='records')[0]
    steps = get_process_steps(round['process_steps'])
    params = get_round_params(search, round_id)
    features = get_feature_importance(dataset.dataset_id, round_id)
    return render_template('round.html', dataset=dataset, round=round, steps=steps, features=features, params=params,
                           cols=params.keys(), refresher=int(time.time()))


@app.route('/get_img_dataset/<string:prm>', methods=['GET'])
def get_img_dataset(prm):
    # retrieves the graph at dataset level from dataset_id;round_id, where dataset_id is dataset id and round_id is round id
    dataset_id, graph_type = prm.split(';')
    return send_file(get_dataset_folder(dataset_id) + '/graphs/_%s.png' % graph_type, mimetype='image/png')


@app.route('/get_img_round/<string:prm>', methods=['GET'])
def get_img_round(prm):
    # retrieves the graph at dataset level from dataset_id;round_id, where dataset_id is dataset id and round_id is round id
    dataset_id, round_id, graph_type = prm.split(';')
    return send_file(get_dataset_folder(dataset_id) + '/graphs/%s_%s.png' % (graph_type, round_id),
                     mimetype='image/png')


@app.route('/create', methods=['GET', 'POST'])
def create():
    # form to create a new dataset
    form = DatasetForm()
    if request.method == 'POST':
        if form.validate():
            try:
                dt = create_dataset(name=form.name.data,
                                    description=form.description.data,
                                    is_uploaded=form.is_uploaded.data,
                                    source=form.source.data,
                                    is_public=form.is_public.data,
                                    url=form.url.data,
                                    problem_type=form.problem_type.data,
                                    metric=form.metric.data,
                                    other_metrics=form.other_metrics.data,
                                    filename_train=form.filename_train.data,
                                    holdout_ratio=form.holdout_ratio.data / 100.,
                                    filename_cols=form.filename_cols.data,
                                    filename_test=form.filename_test.data,
                                    filename_submit=form.filename_submit.data,
                                    col_submit=form.col_submit.data,
                                    cv_folds=form.cv_folds.data,
                                    y_col=form.y_col.data,
                                    val_col=form.val_col.data,
                                    val_col_shuffle=form.val_col_shuffle.data)

                return redirect('index')
            except Exception as e:
                flash(e)
        else:
            flash(", ".join([key+': ' + form.errors[key][0] for key in form.errors.keys()]))

    return render_template('create.html', form=form)


@app.route('/import', methods=['GET', 'POST'])
def import_file():
    # form to import a file of dataset descriptions
    if request.method == 'POST':
        f = request.files['file']
        ext = f.filename.split('.')[-1].lower()
        if ext not in ['csv', 'xls', 'xlsx']:
            flash('file type must be csv, xls or xlsx')
        else:
            if ext == 'csv':
                df = pd.read_csv(f)
            else:
                df = pd.read_excel(f)
            try:
                line_number = 1
                for line in df.fillna('').to_dict(orient='records'):
                    print('creating dataset %s in %s' % (line['name'], line['problem_type']))
                    line['other_metrics'] = line['other_metrics'].replace(' ', '').split(',')
                    create_dataset(**line)
                    line_number += 1
                return redirect('index')
            except Exception as e:
                flash('Error in line %d: %s' % (line_number, str(e)))

    return render_template('import.html')


@app.route('/monitor', methods=['GET', 'POST'])
def monitor():
    # monitor workers
    return render_template('monitor.html', controller=get_heart_beeps('controller'),
                           workers=get_heart_beeps('worker'))
