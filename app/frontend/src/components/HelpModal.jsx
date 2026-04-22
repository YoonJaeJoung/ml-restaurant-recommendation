export default function HelpModal({ open, onClose }) {
  if (!open) return null
  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <div className="content">
          <h2>How this recommender works</h2>
          <p>
            This app combines an embedding-based semantic search over 2.1M Google reviews with an
            aspect-based re-ranker that weighs what you actually care about. The pipeline has five stages.
          </p>

          <h3>1. Sentence embeddings</h3>
          <p>
            Every review is embedded once, offline, using <code>nomic-embed-text-v1.5</code> (768-dim vectors).
            Your query gets the same treatment at request time. Cosine similarity between embeddings measures
            how closely two pieces of text "mean" the same thing.
          </p>

          <h3>2. PCA compression</h3>
          <p>
            768-dim vectors are projected down to 128 dimensions by a fitted PCA. This keeps ~99% of the variance
            but makes per-query retrieval ~99× faster. Both restaurant embeddings and your query get projected
            with the same model.
          </p>

          <h3>3. K-means clusters</h3>
          <p>
            Restaurants are grouped into 50 clusters in PCA space — things like "ramen / broth / pork",
            "date-night / dim-lit / natural-wine", "quick-lunch / counter / deli". On each query we score the
            cluster centroids against your query and only search reviews inside the top-5 clusters — this is
            what drops retrieval from multi-second to sub-second.
          </p>

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
