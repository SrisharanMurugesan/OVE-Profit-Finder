from flask import Flask, request, render_template_string
import pandas as pd
import io

def profit_by_filter(df, mmr_col, price_col, val):
    v = val.strip()
    if v:
        try:
            df = df[(df[mmr_col] - df[price_col]) >= float(v)]
        except:
            pass
    return df

app = Flask(__name__)

INDEX_HTML = """
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>CSV Filter Interface - CR & Buy Now Price</title>
  
  <style>
    body { font-family: Arial, sans-serif; margin:0; padding:0; background:#f7f7f7; }
    header { background:#333; color:#fff; padding:10px 20px; display:flex; justify-content:space-between; }
    header .left, header .right { font-size:14px; }
    main { display:flex; padding:20px; }
    .left-col { width:45%; display:flex; flex-direction:column; }
    .filter-box, .instructions {
      background:#fff; padding:15px; margin-bottom:15px;
      box-shadow:0 0 5px rgba(0,0,0,0.1); border-radius:5px;
    }
    .filter-box h2, .instructions h2 { margin:0 0 10px; color:#333; }
    .filter-group { display:flex; align-items:center; margin-bottom:10px; }
    .filter-group label { width:180px; }
    .filter-group input { padding:4px; font-size:14px; margin:2px; }
    .two-boxes input { width:45%; }
    .instructions ul { padding-left:20px; }
    .right-col { width:45%; display:flex; flex-direction:column; align-items:center; }
    .upload-area {
      width:750px; height:350px;  margin-left: 0; margin-right: -170px; border:2px dashed #ccc; border-radius:10px;
      background:#fff; display:flex; flex-direction:column;
      justify-content:center; align-items:center; position:relative;
      box-shadow:0 0 5px rgba(0,0,0,0.1); cursor:pointer;
    }
    .upload-area.hover { background:#e8e8e8; }
    .upload-area p { margin:5px; color:#333; }
    #file-icon { position:absolute; top:10px; right:10px; font-size:24px; display:none; }
    button { margin-top:10px; padding:5px 10px; font-size:14px; cursor:pointer; }
    #file-input { display:none; }
    /* new: results table styling */
    .results { width:100%; margin-top:20px; background:#fff; padding:15px;
               box-shadow:0 0 5px rgba(0,0,0,0.1); border-radius:5px; }
    .results h2 { margin-top:0; color:#333; }
    .results table { width:100%; border-collapse:collapse; margin-top:10px; }
    .results th, .results td { border:1px solid #ccc; padding:8px; text-align:left; }
    .results th { background:#f0f0f0; }
  </style>
</head>
<body>
  <header>
    <div class="left">Created by Srisharan Murugesan</div>
    <div class="right">How to use: Set CR and Buy Now Price filters &amp; upload CSV</div>
  </header>
  <form id="upload-form" action="/" method="post" enctype="multipart/form-data">
    <main>
      <div class="left-col">
        <div class="filter-box">
          <h2>Filter Settings</h2>
          <div class="filter-group">
            <label for="min_cr">Min CR Value:</label>
            <input type="number" step="0.1" name="min_cr" id="min_cr" placeholder="e.g. 3.0">
          </div>
          <div class="filter-group two-boxes">
            <label>Buy Now Price Range:</label>
            <input type="number" name="min_price" id="min_price" placeholder="Min Price">
            <input type="number" name="max_price" id="max_price" placeholder="Max Price">
          </div>
            <!-- Min Profit filter -->
          <div class="filter-group">
            <label for="profit_by">Min Profit (MMR – Buy Now):</label>
            <input type="number" step="0.01" name="profit_by" id="profit_by" placeholder="e.g. 1000">
          </div>

        </div>
        <div class="instructions">
          <h2>Instructions</h2>
          <ul>
            <li>In OVE, apply any search &amp; click “Export” to get your CSV.</li>
            <li>Set Min CR, Buy Now Price, and other filters.</li>
            <li>Drag that CSV into the box on the right (or click “Select File”).</li>
            <li>Finally, press the <strong>Start Search</strong> button below the box to view results.</li>
          </ul>
        </div>
      </div>
      <div class="right-col">
        <div class="upload-area" id="drop-zone">
          <span id="file-icon">✅</span>
          <p>Drag &amp; drop your CSV file here</p>
          <p>or click to select</p>
          <button type="button" id="upload-button">Select File</button>
          <input type="file" name="file" id="file-input" accept=".csv">
        </div>
        <button type="submit" id="start-button">Start Search</button>
      </div>
    </main>
  </form>

  {% if table_html %}
  <div class="results">
    <h2>Profitable VINs</h2>
    {{ table_html|safe }}
  </div>
  {% endif %}

  <script>
    const dropZone = document.getElementById('drop-zone'),
          fileInput = document.getElementById('file-input'),
          uploadButton = document.getElementById('upload-button'),
          fileIcon = document.getElementById('file-icon');

    function showIcon(){ fileIcon.style.display='block'; }

    dropZone.addEventListener('dragover', e=>{ e.preventDefault(); dropZone.classList.add('hover'); });
    dropZone.addEventListener('dragleave', ()=>dropZone.classList.remove('hover'));
    dropZone.addEventListener('drop', e=>{
      e.preventDefault(); dropZone.classList.remove('hover');
      if(e.dataTransfer.files.length){
        fileInput.files = e.dataTransfer.files;
        showIcon();
      }
    });
    dropZone.addEventListener('click', ()=>fileInput.click());
    uploadButton.addEventListener('click', e=>{ e.stopPropagation(); fileInput.click(); });
    fileInput.addEventListener('change', ()=>{ if(fileInput.files.length) showIcon(); });
  </script>
</body>
</html>
"""

def numeric_min_filter(df, col, val):
    v = val.strip()
    if v:
        try:
            df = df[pd.to_numeric(df[col], errors='coerce') >= float(v)]
        except:
            pass
    return df

def numeric_max_filter(df, col, val):
    v = val.strip()
    if v:
        try:
            df = df[pd.to_numeric(df[col], errors='coerce') <= float(v)]
        except:
            pass
    return df

@app.route('/', methods=['GET', 'POST'])
def index():
    table_html = None

    if request.method == 'POST':
        f = request.files.get('file')
        if f and f.filename:
            df = pd.read_csv(f)
            df['MMR'] = pd.to_numeric(df['MMR'], errors='coerce')
            df['Buy Now Price'] = pd.to_numeric(df['Buy Now Price'], errors='coerce')
            df['Condition Report Grade'] = pd.to_numeric(df['Condition Report Grade'], errors='coerce')
            df = df[df['Buy Now Price'].notna()]
            df = df[df['Buy Now Price'] > 0]

            out = df[df['MMR'] > df['Buy Now Price']]
            form = request.form

            mcr = form.get('min_cr', '').strip()
            if mcr:
                try:
                    out = out[out['Condition Report Grade'] >= float(mcr)]
                except:
                    pass

            out = numeric_min_filter(out, 'Buy Now Price', form.get('min_price', ''))
            out = numeric_max_filter(out, 'Buy Now Price', form.get('max_price', ''))
         
            
            out = profit_by_filter(out, 'MMR', 'Buy Now Price', form.get('profit_by', ''))



            if not out.empty:
                subset = out[['Year','Make', 'Model', 'MMR', 'Buy Now Price', 'Vin']].rename(
                    columns={
                        'Year': 'Year',
                        'Make': 'Brand',
                        'Model': 'Model',
                        'Vin': 'VIN',
                        'MMR': 'MMR',
                        'Buy Now Price': 'Buy Now'
                    }
                )
                table_html = subset.to_html(index=False)
                


    return render_template_string(INDEX_HTML, table_html=table_html)

if __name__ == '__main__':
    app.run(debug=True)
