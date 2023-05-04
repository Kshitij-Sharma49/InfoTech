import csv
import subprocess
from flask import Flask, jsonify, request
# from flask_restful import Api, Resource, reqparse, abort, fields, marshal_with

app = Flask(__name__)
# api = Api(app)

@app.route('/docs_info/<int:doc_id>', methods=['GET'])
def get_sim_docs(doc_id):
    # Open CSV file
    with open('similarities.csv', 'r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            # Check if the row corresponds to the requested doc_id
            if int(row['Doc ID']) == doc_id:
                # If found, return the similarity percentage as JSON response
                sim1 = float(row['Sim1'])*100
                sim2 = float(row['Sim2'])*100
                sim3 = float(row['Sim3'])*100
                sim4 = float(row['Sim4'])*100
                return jsonify({ 'docs': [ int(row['D1']),  int(row['D2']), int(row['D3']), int(row['D4']) ], 
                                'sim': [sim1, sim2, sim3, sim4] })
    
    # If not found, return a 404 error
    return jsonify({'error': 'doc not found'}), 404
    
@app.route('/docs_upload', methods=['POST'])
def add_ipfs_link():
    # Parse the request JSON data
    req_data = request.get_json()
    doc_id = req_data['doc_id']
    ipfs_link = req_data['ipfs_link']

    # Check if the doc_id already exists in the CSV file
    with open('ipfs_links.csv', 'r') as f:
        reader = csv.reader(f)
        for row in reader:
            if row[1] == str(doc_id):
                return jsonify({'message': f"Document with ID {doc_id} already exists."}), 400
    
    # Append the IPFS link to the CSV file
    with open('ipfs_links.csv', mode='a', newline='') as file:
        writer = csv.writer(file)
        # Find the serial no for the new link
        with open('ipfs_links.csv', 'r') as f:
            reader = csv.reader(f)
            serial_no = sum(1 for row in reader)
        writer.writerow([serial_no+1, doc_id, ipfs_link])
    
    # Run another Python script in the same directory
    # subprocess.run(['python', 'similarity.py'])
    
    return jsonify({'message': 'Document added successfully.'}), 200    

# api.add_resource(TestClass, "/next")    

if __name__ == "__main__":
    app.run(debug=True,host='0.0.0.0')