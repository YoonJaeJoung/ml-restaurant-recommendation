export default function HelpModal({ open, onClose }) {
  if (!open) return null
  
  const clusterExamples = [
    { id: 0, name: "BBQ & Soul Food", keywords: "chicken, bbq, order, friendly, rice" },
    { id: 1, name: "Italian Fine Dining", keywords: "pasta, italian, wine, menu, atmosphere" },
    { id: 12, name: "Thai & Asian", keywords: "thai, pad, curry, rice, chicken" },
    { id: 38, name: "Fast Casual Mexican", keywords: "chipotle, burrito, clean, location, fresh" },
    { id: 49, name: "Intimate Bistros", keywords: "italian, pasta, atmosphere, wine, dinner" }
  ]

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <div className="content">
          <h2>How this recommender works</h2>
          <p>
            This app combines an embedding-based semantic search over 2.1M Google reviews with an
            aspect-based re-ranker that weighs what you actually care about. The pipeline has five stages.
          </p>

          <h3>0. Data Collection</h3>
          <p>
            We started with 19,532 NYC restaurants and 2.1M Google reviews from the UCSD Google Local Reviews dataset.
            Raw data was filtered for authentic English reviews (removed CJK characters), grouped by restaurant,
            and downsampled to the top 500 most detailed reviews per location to balance dataset size.
          </p>
          
          <details>
            <summary style={{cursor: 'pointer', fontWeight: 'bold', marginBottom: '12px'}}>
              📄 Raw data example (click to expand)
            </summary>
            <div style={{marginLeft: '12px', marginTop: '12px', backgroundColor: '#f9f9f9', padding: '12px', borderRadius: '6px', fontSize: '12px', fontFamily: 'monospace', overflow: 'auto', maxHeight: '200px', lineHeight: '1.4'}}>
              <div><strong>Restaurant Metadata:</strong></div>
              <div>name: "Eleven Madison Park"</div>
              <div>address: "11 Madison Avenue, New York, NY 10010"</div>
              <div>avg_rating: 4.8</div>
              <div>num_reviews: 2847</div>
              <div>price: "$$$$"</div>
              <div>category: ["American", "Fine Dining"]</div>
              <br/>
              <div><strong>Sample Review:</strong></div>
              <div>"Came here for my anniversary. The tasting menu was absolutely</div>
              <div>exquisite — each course was a work of art. Service was impeccable,</div>
              <div>staff anticipated our needs before we even asked. The wine pairing was</div>
              <div>expertly curated. Definitely worth the price tag. Can't wait to go back!"</div>
              <br/>
              <div><strong>After processing →</strong></div>
              <div>✅ Keeps original English review</div>
              <div>✅ Embeds with nomic-embed-text-v1.5 (768-dim)</div>
              <div>✅ Grouped by restaurant</div>
              <div>✅ Filtered by detail level (length)</div>
            </div>
          </details>

          <h3>1. Sentence embeddings</h3>
          <p>
            Every review is embedded once, offline, using <code>nomic-embed-text-v1.5</code> (768-dim vectors).
            Your query gets the same treatment at request time. Cosine similarity between embeddings measures
            how closely two pieces of text "mean" the same thing.
          </p>

          <h3>2. PCA compression</h3>
          <p>
            768-dim vectors are projected down to 128 dimensions by a fitted PCA. This keeps ~75.5% of the variance
            but makes per-query retrieval ~99× faster. Both restaurant embeddings and your query get projected
            with the same model.
          </p>

          <h3>3. K-means clusters (50 semantic groups)</h3>
          <p>
            Restaurants are grouped into 50 clusters in PCA space — things like "ramen / broth / pork",
            "date-night / dim-lit / natural-wine", "quick-lunch / counter / deli". On each query we score the
            cluster centroids against your query and only search reviews inside the top-5 clusters — this is
            what drops retrieval from multi-second to sub-second.
          </p>
          
          <details>
            <summary style={{cursor: 'pointer', fontWeight: 'bold', marginBottom: '12px'}}>
              📊 Sample cluster profiles (click to expand)
            </summary>
            <div style={{marginLeft: '12px', marginTop: '12px', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px'}}>
              {clusterExamples.map(cluster => (
                <div key={cluster.id} style={{padding: '8px', backgroundColor: '#f5f5f5', borderRadius: '6px', fontSize: '13px'}}>
                  <strong>Cluster {cluster.id}: {cluster.name}</strong>
                  <div style={{marginTop: '4px', color: '#666'}}>
                    {cluster.keywords}
                  </div>
                  <img 
                    src={`/results/clustering/evaluation/wordclouds/cluster_${cluster.id}.png`}
                    alt={`Cluster ${cluster.id} wordcloud`}
                    style={{width: '100%', marginTop: '8px', borderRadius: '4px', maxHeight: '120px', objectFit: 'cover'}}
                  />
                </div>
              ))}
            </div>
          </details>


          <h3>4. Aspect-based sentiment scoring (ABSA)</h3>
          <p>
            Every restaurant has four precomputed sentiment scores (food, service, price, wait-time) between 0 and 1.
            These come from parsing each review's sentences into clauses, matching keyword lemmas against four
            aspect dictionaries, and running VADER sentiment on each clause — then Bayesian-smoothing against a
            global prior so sparsely-reviewed spots don't explode. See <code>src/absa.py</code>.
          </p>

          <h3>5. Ranking formula</h3>
          <p>
            The final score blends three signals:
          </p>
          <p>
            <code>final = α · rating/5  +  β · aspect_weighted  +  γ · log(1+reviews) / global_max</code>
          </p>
          <p>
            where <code>aspect_weighted = Σᵢ wᵢ · aspect_i</code> and <code>wᵢ</code> are user aspect weights
            auto-detected from your query (keywords like "cheap" boost the price weight). The price aspect
            blends 50/50 with the <code>$</code>/<code>$$</code>/<code>$$$</code> Google Maps tier so a cheap
            restaurant gets a bonus independent of what reviewers happen to have written. Defaults: α=0.4 β=0.5 γ=0.1.
          </p>

          <h3>Location & time filters</h3>
          <p>
            Applied <em>after</em> semantic retrieval. Radius uses haversine distance, viewport uses an axis-aligned
            bounding box, and freeform polygon uses a point-in-polygon test. Time filtering parses the Google hours
            strings and drops restaurants that are definitely closed at your target time (unknown hours stay in).
          </p>

          <div className="modal-footer">
            <button className="btn primary" onClick={onClose}>Got it</button>
          </div>
        </div>
      </div>
    </div>
  )
}
