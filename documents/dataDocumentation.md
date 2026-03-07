# Google Local Data (2021)

**Source:** <https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/>

[Tianyang Zhang](https://www.linkedin.com/in/tianyang-zhang-sky/), UCSD
[Jiacheng Li](https://jiachengli1995.github.io/), UCSD

## Description

This Dataset contains review information on Google map (ratings, text, images, etc.), business metadata (address, geographical info, descriptions, category information, price, open hours, and MISC info), and links (relative businesses) up to Sep 2021 in the United States.

## Citation

Please cite the following papers if you use the data in any way:

- **UCTopic: Unsupervised Contrastive Learning for Phrase Representations and Topic Mining**
  Jiacheng Li, Jingbo Shang, Julian McAuley
  Annual Meeting of the Association for Computational Linguistics (ACL), 2022
  [pdf](https://aclanthology.org/2022.acl-long.426.pdf)

- **Personalized Showcases: Generating Multi-Modal Explanations for Recommendations**
  An Yan, Zhankui He, Jiacheng Li, Tianyang Zhang, Julian Mcauley
  The 46th International ACM SIGIR Conference on Research and Development in Information Retrieval (SIGIR), 2023
  [pdf](https://arxiv.org/pdf/2207.00422.pdf)

## Contact

Jiacheng Li (j9li@eng.ucsd.edu)

## Directory

- [Files](#files)
  - [Complete data](#complete-review-data)
  - [K-cores and ratings-only data](#small-subsets-for-experimentation)
  - [Sample review](#sample-review)
  - [Sample metadata](#sample-metadata)
- [Code](#code)

---

## Files

### Complete review data

> Please only download these (large!) files if you really need them. We recommend using the smaller datasets (i.e. k-core and CSV files) as shown in the [next section](#small-subsets-for-experimentation).

| State | Reviews | Metadata |
|---|---|---|
| Alabama | [reviews](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/review-Alabama.json.gz) | [metadata](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/meta-Alabama.json.gz) |
| Alaska | [reviews](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/review-Alaska.json.gz) | [metadata](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/meta-Alaska.json.gz) |
| Arizona | [reviews](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/review-Arizona.json.gz) | [metadata](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/meta-Arizona.json.gz) |
| Arkansas | [reviews](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/review-Arkansas.json.gz) | [metadata](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/meta-Arkansas.json.gz) |
| California | [reviews](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/review-California.json.gz) | [metadata](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/meta-California.json.gz) |
| Colorado | [reviews](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/review-Colorado.json.gz) | [metadata](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/meta-Colorado.json.gz) |
| Connecticut | [reviews](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/review-Connecticut.json.gz) | [metadata](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/meta-Connecticut.json.gz) |
| Delaware | [reviews](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/review-Delaware.json.gz) | [metadata](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/meta-Delaware.json.gz) |
| District of Columbia | [reviews](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/review-District_of_Columbia.json.gz) | [metadata](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/meta-District_of_Columbia.json.gz) |
| Florida | [reviews](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/review-Florida.json.gz) | [metadata](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/meta-Florida.json.gz) |
| Georgia | [reviews](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/review-Georgia.json.gz) | [metadata](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/meta-Georgia.json.gz) |
| Hawaii | [reviews](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/review-Hawaii.json.gz) | [metadata](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/meta-Hawaii.json.gz) |
| Idaho | [reviews](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/review-Idaho.json.gz) | [metadata](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/meta-Idaho.json.gz) |
| Illinois | [reviews](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/review-Illinois.json.gz) | [metadata](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/meta-Illinois.json.gz) |
| Indiana | [reviews](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/review-Indiana.json.gz) | [metadata](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/meta-Indiana.json.gz) |
| Iowa | [reviews](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/review-Iowa.json.gz) | [metadata](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/meta-Iowa.json.gz) |
| Kansas | [reviews](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/review-Kansas.json.gz) | [metadata](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/meta-Kansas.json.gz) |
| Kentucky | [reviews](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/review-Kentucky.json.gz) | [metadata](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/meta-Kentucky.json.gz) |
| Louisiana | [reviews](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/review-Louisiana.json.gz) | [metadata](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/meta-Louisiana.json.gz) |
| Maine | [reviews](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/review-Maine.json.gz) | [metadata](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/meta-Maine.json.gz) |
| Maryland | [reviews](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/review-Maryland.json.gz) | [metadata](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/meta-Maryland.json.gz) |
| Massachusetts | [reviews](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/review-Massachusetts.json.gz) | [metadata](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/meta-Massachusetts.json.gz) |
| Michigan | [reviews](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/review-Michigan.json.gz) | [metadata](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/meta-Michigan.json.gz) |
| Minnesota | [reviews](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/review-Minnesota.json.gz) | [metadata](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/meta-Minnesota.json.gz) |
| Mississippi | [reviews](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/review-Mississippi.json.gz) | [metadata](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/meta-Mississippi.json.gz) |
| Missouri | [reviews](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/review-Missouri.json.gz) | [metadata](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/meta-Missouri.json.gz) |
| Montana | [reviews](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/review-Montana.json.gz) | [metadata](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/meta-Montana.json.gz) |
| Nebraska | [reviews](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/review-Nebraska.json.gz) | [metadata](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/meta-Nebraska.json.gz) |
| Nevada | [reviews](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/review-Nevada.json.gz) | [metadata](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/meta-Nevada.json.gz) |
| New Hampshire | [reviews](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/review-New_Hampshire.json.gz) | [metadata](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/meta-New_Hampshire.json.gz) |
| New Jersey | [reviews](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/review-New_Jersey.json.gz) | [metadata](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/meta-New_Jersey.json.gz) |
| New Mexico | [reviews](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/review-New_Mexico.json.gz) | [metadata](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/meta-New_Mexico.json.gz) |
| New York | [reviews](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/review-New_York.json.gz) | [metadata](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/meta-New_York.json.gz) |
| North Carolina | [reviews](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/review-North_Carolina.json.gz) | [metadata](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/meta-North_Carolina.json.gz) |
| North Dakota | [reviews](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/review-North_Dakota.json.gz) | [metadata](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/meta-North_Dakota.json.gz) |
| Ohio | [reviews](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/review-Ohio.json.gz) | [metadata](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/meta-Ohio.json.gz) |
| Oklahoma | [reviews](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/review-Oklahoma.json.gz) | [metadata](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/meta-Oklahoma.json.gz) |
| Oregon | [reviews](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/review-Oregon.json.gz) | [metadata](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/meta-Oregon.json.gz) |
| Pennsylvania | [reviews](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/review-Pennsylvania.json.gz) | [metadata](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/meta-Pennsylvania.json.gz) |
| Rhode Island | [reviews](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/review-Rhode_Island.json.gz) | [metadata](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/meta-Rhode_Island.json.gz) |
| South Carolina | [reviews](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/review-South_Carolina.json.gz) | [metadata](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/meta-South_Carolina.json.gz) |
| South Dakota | [reviews](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/review-South_Dakota.json.gz) | [metadata](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/meta-South_Dakota.json.gz) |
| Tennessee | [reviews](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/review-Tennessee.json.gz) | [metadata](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/meta-Tennessee.json.gz) |
| Texas | [reviews](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/review-Texas.json.gz) | [metadata](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/meta-Texas.json.gz) |
| Utah | [reviews](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/review-Utah.json.gz) | [metadata](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/meta-Utah.json.gz) |
| Vermont | [reviews](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/review-Vermont.json.gz) | [metadata](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/meta-Vermont.json.gz) |
| Virginia | [reviews](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/review-Virginia.json.gz) | [metadata](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/meta-Virginia.json.gz) |
| Washington | [reviews](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/review-Washington.json.gz) | [metadata](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/meta-Washington.json.gz) |
| West Virginia | [reviews](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/review-West_Virginia.json.gz) | [metadata](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/meta-West_Virginia.json.gz) |
| Wisconsin | [reviews](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/review-Wisconsin.json.gz) | [metadata](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/meta-Wisconsin.json.gz) |
| Wyoming | [reviews](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/review-Wyoming.json.gz) | [metadata](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/meta-Wyoming.json.gz) |
| Other | [reviews](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/review-other.json.gz) | [metadata](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/meta-other.json.gz) |

---

### "Small" subsets for experimentation

If you're using this data for a class project (or similar) please consider using one of these smaller datasets below before requesting the larger files.

- **K-cores** (i.e., dense subsets): These data have been reduced to extract the [k-core](https://en.wikipedia.org/wiki/Degeneracy_(graph_theory)), such that each of the remaining users and items have k reviews each.
- **Ratings only**: These datasets include no metadata or reviews, but only (business, user, rating, timestamp) tuples. Thus they are suitable for use with [mymedialite](http://www.mymedialite.net/) (or similar) packages.

You can directly download the following smaller per-category datasets:

| State | 10-core | Reviews Count | Ratings Only | Ratings Count |
|---|---|---|---|---|
| Alabama | [10-core](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/review-Alabama_10.json.gz) | 5,146,330 | [ratings only](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/rating-Alabama.csv.gz) | 8,967,499 |
| Alaska | [10-core](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/review-Alaska_10.json.gz) | 521,515 | [ratings only](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/rating-Alaska.csv.gz) | 1,051,246 |
| Arizona | [10-core](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/review-Arizona_10.json.gz) | 10,764,435 | [ratings only](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/rating-Arizona.csv.gz) | 18,375,050 |
| Arkansas | [10-core](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/review-Arkansas_10.json.gz) | 2,855,468 | [ratings only](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/rating-Arkansas.csv.gz) | 5,106,056 |
| California | [10-core](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/review-California_10.json.gz) | 44,476,890 | [ratings only](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/rating-California.csv.gz) | 70,529,977 |
| Colorado | [10-core](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/review-Colorado_10.json.gz) | 8,738,271 | [ratings only](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/rating-Colorado.csv.gz) | 15,681,222 |
| Connecticut | [10-core](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/review-Connecticut_10.json.gz) | 2,680,107 | [ratings only](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/rating-Connecticut.csv.gz) | 5,181,800 |
| Delaware | [10-core](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/review-Delaware_10.json.gz) | 905,537 | [ratings only](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/rating-Delaware.csv.gz) | 1,885,948 |
| District of Columbia | [10-core](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/review-District_of_Columbia_10.json.gz) | 564,783 | [ratings only](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/rating-District_of_Columbia.csv.gz) | 1,894,317 |
| Florida | [10-core](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/review-Florida_10.json.gz) | 35,457,319 | [ratings only](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/rating-Florida.csv.gz) | 61,803,524 |
| Georgia | [10-core](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/review-Georgia_10.json.gz) | 13,599,687 | [ratings only](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/rating-Georgia.csv.gz) | 24,060,125 |
| Hawaii | [10-core](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/review-Hawaii_10.json.gz) | 1,504,347 | [ratings only](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/rating-Hawaii.csv.gz) | 3,111,531 |
| Idaho | [10-core](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/review-Idaho_10.json.gz) | 2,085,487 | [ratings only](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/rating-Idaho.csv.gz) | 3,892,636 |
| Illinois | [10-core](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/review-Illinois_10.json.gz) | 13,237,848 | [ratings only](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/rating-Illinois.csv.gz) | 23,096,838 |
| Indiana | [10-core](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/review-Indiana_10.json.gz) | 7,638,803 | [ratings only](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/rating-Indiana.csv.gz) | 12,865,167 |
| Iowa | [10-core](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/review-Iowa_10.json.gz) | 2,677,684 | [ratings only](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/rating-Iowa.csv.gz) | 4,838,887 |
| Kansas | [10-core](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/review-Kansas_10.json.gz) | 3,080,115 | [ratings only](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/rating-Kansas.csv.gz) | 5,546,880 |
| Kentucky | [10-core](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/review-Kentucky_10.json.gz) | 4,240,662 | [ratings only](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/rating-Kentucky.csv.gz) | 7,654,993 |
| Louisiana | [10-core](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/review-Louisiana_10.json.gz) | 3,985,782 | [ratings only](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/rating-Louisiana.csv.gz) | 7,536,078 |
| Maine | [10-core](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/review-Maine_10.json.gz) | 1,123,881 | [ratings only](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/rating-Maine.csv.gz) | 2,214,773 |
| Maryland | [10-core](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/review-Maryland_10.json.gz) | 5,590,890 | [ratings only](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/rating-Maryland.csv.gz) | 10,728,483 |
| Massachusetts | [10-core](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/review-Massachusetts_10.json.gz) | 5,624,944 | [ratings only](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/rating-Massachusetts.csv.gz) | 10,447,007 |
| Michigan | [10-core](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/review-Michigan_10.json.gz) | 13,212,364 | [ratings only](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/rating-Michigan.csv.gz) | 20,776,155 |
| Minnesota | [10-core](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/review-Minnesota_10.json.gz) | 5,646,319 | [ratings only](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/rating-Minnesota.csv.gz) | 9,520,258 |
| Mississippi | [10-core](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/review-Mississippi_10.json.gz) | 1,971,181 | [ratings only](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/rating-Mississippi.csv.gz) | 3,861,771 |
| Missouri | [10-core](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/review-Missouri_10.json.gz) | 7,863,559 | [ratings only](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/rating-Missouri.csv.gz) | 13,416,511 |
| Montana | [10-core](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/review-Montana_10.json.gz) | 950,370 | [ratings only](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/rating-Montana.csv.gz) | 1,933,939 |
| Nebraska | [10-core](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/review-Nebraska_10.json.gz) | 1,817,866 | [ratings only](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/rating-Nebraska.csv.gz) | 3,286,810 |
| Nevada | [10-core](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/review-Nevada_10.json.gz) | 4,170,080 | [ratings only](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/rating-Nevada.csv.gz) | 8,833,403 |
| New Hampshire | [10-core](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/review-New_Hampshire_10.json.gz) | 1,296,603 | [ratings only](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/rating-New_Hampshire.csv.gz) | 2,648,081 |
| New Jersey | [10-core](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/review-New_Jersey_10.json.gz) | 8,227,961 | [ratings only](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/rating-New_Jersey.csv.gz) | 15,720,266 |
| New Mexico | [10-core](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/review-New_Mexico_10.json.gz) | 2,571,363 | [ratings only](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/rating-New_Mexico.csv.gz) | 4,705,389 |
| New York | [10-core](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/review-New_York_10.json.gz) | 18,661,975 | [ratings only](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/rating-New_York.csv.gz) | 33,459,761 |
| North Carolina | [10-core](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/review-North_Carolina_10.json.gz) | 12,905,081 | [ratings only](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/rating-North_Carolina.csv.gz) | 22,299,136 |
| North Dakota | [10-core](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/review-North_Dakota_10.json.gz) | 563,693 | [ratings only](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/rating-North_Dakota.csv.gz) | 1,109,558 |
| Ohio | [10-core](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/review-Ohio_10.json.gz) | 14,506,563 | [ratings only](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/rating-Ohio.csv.gz) | 23,039,365 |
| Oklahoma | [10-core](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/review-Oklahoma_10.json.gz) | 5,011,462 | [ratings only](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/rating-Oklahoma.csv.gz) | 8,482,820 |
| Oregon | [10-core](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/review-Oregon_10.json.gz) | 6,270,332 | [ratings only](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/rating-Oregon.csv.gz) | 11,012,170 |
| Pennsylvania | [10-core](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/review-Pennsylvania_10.json.gz) | 12,772,358 | [ratings only](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/rating-Pennsylvania.csv.gz) | 21,944,802 |
| Rhode Island | [10-core](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/review-Rhode_Island_10.json.gz) | 890,006 | [ratings only](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/rating-Rhode_Island.csv.gz) | 1,777,094 |
| South Carolina | [10-core](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/review-South_Carolina_10.json.gz) | 6,504,999 | [ratings only](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/rating-South_Carolina.csv.gz) | 11,995,482 |
| South Dakota | [10-core](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/review-South_Dakota_10.json.gz) | 673,048 | [ratings only](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/rating-South_Dakota.csv.gz) | 1,452,599 |
| Tennessee | [10-core](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/review-Tennessee_10.json.gz) | 8,855,714 | [ratings only](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/rating-Tennessee.csv.gz) | 15,951,213 |
| Texas | [10-core](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/review-Texas_10.json.gz) | 40,696,824 | [ratings only](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/rating-Texas.csv.gz) | 66,435,184 |
| Utah | [10-core](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/review-Utah_10.json.gz) | 4,933,807 | [ratings only](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/rating-Utah.csv.gz) | 9,081,167 |
| Vermont | [10-core](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/review-Vermont_10.json.gz) | 324,725 | [ratings only](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/rating-Vermont.csv.gz) | 852,203 |
| Virginia | [10-core](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/review-Virginia_10.json.gz) | 8,562,059 | [ratings only](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/rating-Virginia.csv.gz) | 15,957,938 |
| Washington | [10-core](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/review-Washington_10.json.gz) | 10,192,020 | [ratings only](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/rating-Washington.csv.gz) | 16,541,734 |
| West Virginia | [10-core](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/review-West_Virginia_10.json.gz) | 1,080,333 | [ratings only](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/rating-West_Virginia.csv.gz) | 2,208,199 |
| Wisconsin | [10-core](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/review-Wisconsin_10.json.gz) | 6,036,482 | [ratings only](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/rating-Wisconsin.csv.gz) | 10,246,685 |
| Wyoming | [10-core](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/review-Wyoming_10.json.gz) | 427,808 | [ratings only](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/rating-Wyoming.csv.gz) | 1,141,421 |

---

### Data format

Format is one-review-per-line in json. See examples below for further help reading the data.

### Sample review:

- `user_id` - ID of the reviewer
- `name` - name of the reviewer
- `time` - time of the review (unix time)
- `rating` - rating of the business
- `text` - text of the review
- `pics` - pictures of the review
- `resp` - business response to the review including unix time and text of the response
- `gmap_id` - ID of the business

### Sample metadata:

- `name` - name of the business
- `address` - address of the business
- `gmap_id` - ID of the business
- `description` - description of the business
- `latitude` - latitude of the business
- `longitude` - longitude of the business
- `category` - category of the business
- `avg_rating` - average rating of the business
- `num_of_reviews` - number of reviews
- `price` - price of the business
- `hours` - open hours
- `MISC` - MISC information
- `state` - the current status of the business (e.g., permanently closed)
- `relative_results` - relative businesses recommended by Google
- `url` - URL of the business

---

## Code

### Reading the data

Data can be treated as python dictionary objects. A simple script to read any of the above data is as follows:

```python
import json
import gzip

# For .json.gz files
def parse(path):
    g = gzip.open(path, 'r')
    for l in g:
        yield json.loads(l)
```
