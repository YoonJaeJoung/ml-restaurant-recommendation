import { IconGithub } from './Icons.jsx'

const GITHUB_URL = 'https://github.com/andrewjoung/ml-restaurant-recommendation'
const TEAM = ['Ashley Ying', 'Jake Lipner', 'Langyue Zhao', 'Yiduo Lu', 'Yoonjae Andrew Joung']

export default function AboutModal({ open, onClose }) {
  if (!open) return null
  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <div className="content">
          <h2>Noble Jaguars</h2>
          <p style={{ fontFamily: 'var(--mono)', fontSize: 11, letterSpacing: 1.6, textTransform: 'uppercase', color: 'var(--muted)', marginTop: -4 }}>
            Final project · NYU Fundamentals of Machine Learning
          </p>

          <h3>The team</h3>
          <p>{TEAM.join(' · ')}</p>

          <h3>Project overview</h3>
          <p>
            Finding a restaurant today is slow and imprecise. Users either trawl through
            star ratings on a map, or sift through reviews and photos by hand. Traditional
            recommenders lean on collaborative filtering or aggregate ratings, ignoring
            the rich signal hiding inside review text.
          </p>
          <p>
            Noble Jaguars builds a <strong>context-aware restaurant recommender</strong> over
            the <a className="link" href="https://cseweb.ucsd.edu/~jmcauley/datasets.html#google_local" target="_blank" rel="noreferrer">Google Local Reviews</a> dataset — 19,500 NYC restaurants, 2.1M reviews — and
            lets you search in natural language while weighing exactly the aspects you care
            about (food, service, price, wait time).
          </p>

          <h3>What&rsquo;s under the hood</h3>
          <p>
            Sentence embeddings (nomic-embed-text-v1.5) · PCA (768&rarr;128) · K-means over 50
            clusters for fast cluster-scoped retrieval · Aspect-based sentiment analysis (VADER +
            Bayesian smoothing) · and a weighted ranker that blends rating, aspect fit, and
            review volume. Tap the <strong>?</strong> button top-right for the full pipeline math.
          </p>

          <div className="modal-footer" style={{ justifyContent: 'space-between' }}>
            <a
              className="btn outline"
              href={GITHUB_URL}
              target="_blank"
              rel="noreferrer"
              style={{ gap: 8 }}
            >
              <IconGithub size={16} />
              View on GitHub
            </a>
            <button className="btn primary" onClick={onClose}>Close</button>
          </div>
        </div>
      </div>
    </div>
  )
}
