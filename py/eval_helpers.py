import numpy as np
import sys
import os
import json
import glob

class Joint:
    def __init__(self):
        self.count = 15
        self.right_ankle = 0
        self.right_knee = 1
        self.right_hip = 2
        self.left_hip = 3
        self.left_knee = 4
        self.left_ankle = 5
        self.right_wrist = 6
        self.right_elbow = 7
        self.right_shoulder = 8
        self.left_shoulder = 9
        self.left_elbow = 10
        self.left_wrist = 11
        self.neck = 12
        self.nose = 13
        self.head_top = 14

        self.name = {}
        self.name[self.right_ankle]    = "right_ankle"
        self.name[self.right_knee]     = "right_knee"
        self.name[self.right_hip]      = "right_hip"
        self.name[self.right_shoulder] = "right_shoulder"
        self.name[self.right_elbow]    = "right_elbow"
        self.name[self.right_wrist]    = "right_wrist"
        self.name[self.left_ankle]     = "left_ankle"
        self.name[self.left_knee]      = "left_knee"
        self.name[self.left_hip]       = "left_hip"
        self.name[self.left_shoulder]  = "left_shoulder"
        self.name[self.left_elbow]     = "left_elbow"
        self.name[self.left_wrist]     = "left_wrist"
        self.name[self.neck]           = "neck"
        self.name[self.nose]           = "nose"
        self.name[self.head_top]       = "head_top"

        self.symmetric_joint = {}
        self.symmetric_joint[self.right_ankle]    = self.left_ankle
        self.symmetric_joint[self.right_knee]     = self.left_knee
        self.symmetric_joint[self.right_hip]      = self.left_hip
        self.symmetric_joint[self.right_shoulder] = self.left_shoulder
        self.symmetric_joint[self.right_elbow]    = self.left_elbow
        self.symmetric_joint[self.right_wrist]    = self.left_wrist
        self.symmetric_joint[self.left_ankle]     = self.right_ankle
        self.symmetric_joint[self.left_knee]      = self.right_knee
        self.symmetric_joint[self.left_hip]       = self.right_hip
        self.symmetric_joint[self.left_shoulder]  = self.right_shoulder
        self.symmetric_joint[self.left_elbow]     = self.right_elbow
        self.symmetric_joint[self.left_wrist]     = self.right_wrist
        self.symmetric_joint[self.neck]           = -1
        self.symmetric_joint[self.nose]           = -1
        self.symmetric_joint[self.head_top]       = -1


def getPointGTbyID(points,pidx):

    point = []
    for i in range(len(points)):
        if (points[i]["id"] != None and points[i]["id"][0] == pidx): # if joint id matches
            point = points[i]
            break

    return point


def getHeadSize(x1,y1,x2,y2):
    headSize = 0.6*np.linalg.norm(np.subtract([x2,y2],[x1,y1]));
    return headSize


def formatCell(val,delim):
    return "{:>5}".format("%1.1f" % val) + delim


def getHeader():
    strHeader = "&"
    strHeader += " Head &"
    strHeader += " Shou &"
    strHeader += " Elb  &"
    strHeader += " Wri  &"
    strHeader += " Hip  &"
    strHeader += " Knee &"
    strHeader += " Ankl &"
    strHeader += " Total%s" % ("\\"+"\\")
    return strHeader


def getMotHeader():
    strHeader = "&"
    strHeader += " MOTA &"
    strHeader += " MOTA &"
    strHeader += " MOTA &"
    strHeader += " MOTA &"
    strHeader += " MOTA &"
    strHeader += " MOTA &"
    strHeader += " MOTA &"
    strHeader += " MOTA &"
    strHeader += " MOTP &"
    strHeader += " Prec &"
    strHeader += " Rec  %s\n" % ("\\"+"\\")
    strHeader += "&"
    strHeader += " Head &"
    strHeader += " Shou &"
    strHeader += " Elb  &"
    strHeader += " Wri  &"
    strHeader += " Hip  &"
    strHeader += " Knee &"
    strHeader += " Ankl &"
    strHeader += " Total&"
    strHeader += " Total&"
    strHeader += " Total&"
    strHeader += " Total%s" % ("\\"+"\\")

    return strHeader


def getCum(vals):
    cum = []; n = -1
    cum += [(vals[[Joint().head_top,      Joint().neck,        Joint().nose],0].mean())]
    cum += [(vals[[Joint().right_shoulder,Joint().left_shoulder],0].mean())]
    cum += [(vals[[Joint().right_elbow,   Joint().left_elbow   ],0].mean())]
    cum += [(vals[[Joint().right_wrist,   Joint().left_wrist   ],0].mean())]
    cum += [(vals[[Joint().right_hip,     Joint().left_hip     ],0].mean())]
    cum += [(vals[[Joint().right_knee,    Joint().left_knee    ],0].mean())]
    cum += [(vals[[Joint().right_ankle,   Joint().left_ankle   ],0].mean())]
    for i in range(Joint().count,len(vals)):
        cum += [vals[i,0]]
    return cum


def getFormatRow(cum):
    row = "&"
    for i in range(len(cum)-1):
        row += formatCell(cum[i]," &")
    row += formatCell(cum[len(cum)-1],(" %s" % "\\"+"\\"))
    return row


def printTable(vals,motHeader=False):

    cum = getCum(vals)
    row = getFormatRow(cum)
    if (motHeader):
        header = getMotHeader()
    else:
        header = getHeader()
    print header
    print row
    return header+"\n", row+"\n"


def printTableTracking(valsPerPart):

    cum = getCum(vals)
    row = getFormatRow(cum)
    print getHeader()
    print row
    return getHeader()+"\n", row+"\n"


# compute recall/precision curve (RPC) values
def computeRPC(scores,labels,totalPos):

    precision = np.zeros(len(scores))
    recall    = np.zeros(len(scores))
    npos = 0;

    idxsSort = np.array(scores).argsort()[::-1]
    labelsSort = labels[idxsSort];

    for sidx in range(len(idxsSort)):
        if (labelsSort[sidx] == 1):
            npos += 1
        # recall: how many true positives were found out of the total number of positives?
        recall[sidx]    = 1.0*npos / totalPos
        # precision: how many true positives were found out of the total number of samples?
        precision[sidx] = 1.0*npos / (sidx + 1)

    return precision, recall, idxsSort


# compute Average Precision using recall/precision values
def VOCap(rec,prec):

    mpre = np.zeros([1,2+len(prec)])
    mpre[0,1:len(prec)+1] = prec
    mrec = np.zeros([1,2+len(rec)])
    mrec[0,1:len(rec)+1] = rec
    mrec[0,len(rec)+1] = 1.0

    for i in range(mpre.size-2,-1,-1):
        mpre[0,i] = max(mpre[0,i],mpre[0,i+1])

    i = np.argwhere( ~np.equal( mrec[0,1:], mrec[0,:mrec.shape[1]-1]) )+1
    i = i.flatten()

    # compute area under the curve
    ap = np.sum( np.multiply( np.subtract( mrec[0,i], mrec[0,i-1]), mpre[0,i] ) )

    return ap

def get_data_dir():
  dataDir = "./"
  return dataDir

def help(msg=''):
  sys.stderr.write(msg +
        'Usage: python evaluate.py <GT_FILE> <PRED_FILE> [MODE]\n\n'
        'GT_FILE   denotes path to json file with annotations.\n'
        'PRED_FILE denotes path to json file with predictions.\n'
        'MODE <frame|multi> Single-frame or multi-frame (default) evaluation.\n')

  exit()

def process_arguments(argv):

  mode = 'multi'

  if len(argv) > 3:
    mode   = str.lower(argv[3])
  elif len(argv)<3 or len(argv)>4:
    help()

  gt_file = argv[1]
  pred_file = argv[2]

  if not os.path.exists(gt_file):
    help('Given ground truth directory does not exist!\n')

  if not os.path.exists(pred_file):
    help('Given prediction directory does not exist!\n')

  return gt_file, pred_file, mode

def process_arguments_server(argv):
  mode = 'multi'

  assert len(argv) == 9, "Wrong number of arguments"

  mode   = str.lower(argv[3])
  gt_dir = argv[1]
  pred_dir = argv[2]
  shortname = argv[4]
  chl = argv[5]
  shortname_uid = argv[6]
  shakey = argv[7]
  timestamp = argv[8]
  if not os.path.exists(gt_dir):
    help('Given ground truth does not exist!\n')

  if not os.path.exists(pred_dir):
    help('Given prediction does not exist!\n')

  return gt_dir, pred_dir, mode, shortname, chl, shortname_uid, shakey, timestamp


def load_data(argv):

  dataDir = get_data_dir()

  gt_file, pred_file, mode = process_arguments(argv)
  gtFilename = dataDir + gt_file
  predFilename = dataDir + pred_file

  # load ground truth (GT)
  with open(gtFilename) as data_file:
      data = json.load(data_file)
  gtFramesAll = data

  # load predictions
  with open(predFilename) as data_file:
      data = json.load(data_file)
  prFramesAll = data

  return gtFramesAll, prFramesAll


def cleanupData(gtFramesAll,prFramesAll):

  # remove all GT frames with empty annorects and remove corresponding entries from predictions
  imgidxs = []
  for imgidx in range(len(gtFramesAll)):
    if (len(gtFramesAll[imgidx]["annorect"]) > 0):
      imgidxs += [imgidx]
  gtFramesAll = [gtFramesAll[imgidx] for imgidx in imgidxs]
  prFramesAll = [prFramesAll[imgidx] for imgidx in imgidxs]

  # remove all gt rectangles that do not have annotations
  for imgidx in range(len(gtFramesAll)):
    gtFramesAll[imgidx]["annorect"] = removeRectsWithoutPoints(gtFramesAll[imgidx]["annorect"])
    prFramesAll[imgidx]["annorect"] = removeRectsWithoutPoints(prFramesAll[imgidx]["annorect"])

  return gtFramesAll, prFramesAll


def removeRectsWithoutPoints(rects):

  idxsPr = []
  for ridxPr in range(len(rects)):
    if (("annopoints" in rects[ridxPr].keys()) and
        (len(rects[ridxPr]["annopoints"]) > 0) and
        ("point" in rects[ridxPr]["annopoints"][0].keys())):
        idxsPr += [ridxPr];
  rects = [rects[ridx] for ridx in idxsPr]
  return rects


def load_data_dir(argv):

  gt_dir, pred_dir, mode = process_arguments(argv)
  if not os.path.exists(gt_dir):
    help('Given GT directory ' + gt_dir + ' does not exist!\n')
  if not os.path.exists(pred_dir):
    help('Given prediction directory ' + pred_dir + ' does not exist!\n')
  filenames = glob.glob(gt_dir + "/*.json")
  gtFramesAll = []
  prFramesAll = []

  for i in range(len(filenames)):
    # load each annotation json file
    with open(filenames[i]) as data_file:
      data = json.load(data_file)
    gt = data["annolist"]
    for imgidx in range(len(gt)):
        gt[imgidx]["seq_id"] = i
    gtFramesAll += gt
    gtBasename = os.path.basename(filenames[i])
    predFilename = pred_dir + gtBasename

    if (not os.path.exists(predFilename)):
        raise IOError('Prediction file ' + predFilename + ' does not exist')

    # load predictions
    with open(predFilename) as data_file:
      data = json.load(data_file)
    pr = data["annolist"]
    if (len(pr) <> len(gt)):
        raise Exception('# prediction frames %d <> # GT frames %d for %s' % (len(pr),len(gt),predFilename))
    prFramesAll += pr

  gtFramesAll,prFramesAll = cleanupData(gtFramesAll,prFramesAll)

  return gtFramesAll, prFramesAll


def writeJson(val,fname):
  with open(fname, 'w') as data_file:
    json.dump(val, data_file)


def assignGTmulti(gtFrames, prFrames, distThresh):
    assert (len(gtFrames) == len(prFrames))

    nJoints = Joint().count
    # part detection scores
    scoresAll = {}
    # positive / negative labels
    labelsAll = {}
    # number of annotated GT joints per image
    nGTall = np.zeros([nJoints, len(gtFrames)])
    for pidx in range(nJoints):
        scoresAll[pidx] = {}
        labelsAll[pidx] = {}
        for imgidx in range(len(gtFrames)):
            scoresAll[pidx][imgidx] = np.zeros([0, 0], dtype=np.float32)
            labelsAll[pidx][imgidx] = np.zeros([0, 0], dtype=np.int8)

    # GT track IDs
    trackidxGT = []

    # prediction track IDs
    trackidxPr = []

    # number of GT poses
    nGTPeople = np.zeros((len(gtFrames), 1))
    # number of predicted poses
    nPrPeople = np.zeros((len(gtFrames), 1))

    # container to save info for computing MOT metrics
    motAll = {}

    for imgidx in range(len(gtFrames)):

        # distance between predicted and GT joints
        dist = np.full((len(prFrames[imgidx]["annorect"]), len(gtFrames[imgidx]["annorect"]), nJoints), np.inf)
        # score of the predicted joint
        score = np.full((len(prFrames[imgidx]["annorect"]), nJoints), np.nan)
        # body joint prediction exist
        hasPr = np.zeros((len(prFrames[imgidx]["annorect"]), nJoints), dtype=bool)
        # body joint is annotated
        hasGT = np.zeros((len(gtFrames[imgidx]["annorect"]), nJoints), dtype=bool)

        trackidxGT = []
        trackidxPr = []
        idxsPr = []
        for ridxPr in range(len(prFrames[imgidx]["annorect"])):
            if (("annopoints" in prFrames[imgidx]["annorect"][ridxPr].keys()) and
                ("point" in prFrames[imgidx]["annorect"][ridxPr]["annopoints"][0].keys())):
                idxsPr += [ridxPr];
        prFrames[imgidx]["annorect"] = [prFrames[imgidx]["annorect"][ridx] for ridx in idxsPr]

        nPrPeople[imgidx, 0] = len(prFrames[imgidx]["annorect"])
        nGTPeople[imgidx, 0] = len(gtFrames[imgidx]["annorect"])
        # iterate over GT poses
        for ridxGT in range(len(gtFrames[imgidx]["annorect"])):
            # GT pose
            rectGT = gtFrames[imgidx]["annorect"][ridxGT]
            if ("track_id" in rectGT.keys()):
                trackidxGT += [rectGT["track_id"][0]]
            pointsGT = []
            if len(rectGT["annopoints"]) > 0:
                pointsGT = rectGT["annopoints"][0]["point"]
            # iterate over all possible body joints
            for i in range(nJoints):
                # GT joint in LSP format
                ppGT = getPointGTbyID(pointsGT, i)
                if len(ppGT) > 0:
                    hasGT[ridxGT, i] = True

        # iterate over predicted poses
        for ridxPr in range(len(prFrames[imgidx]["annorect"])):
            # predicted pose
            rectPr = prFrames[imgidx]["annorect"][ridxPr]
            if ("track_id" in rectPr.keys()):
                trackidxPr += [rectPr["track_id"][0]]
            pointsPr = rectPr["annopoints"][0]["point"]
            for i in range(nJoints):
                # predicted joint in LSP format
                ppPr = getPointGTbyID(pointsPr, i)
                if len(ppPr) > 0:
                    assert("score" in ppPr.keys() and "keypoint score is missing")
                    score[ridxPr, i] = ppPr["score"][0]
                    hasPr[ridxPr, i] = True

        if len(prFrames[imgidx]["annorect"]) and len(gtFrames[imgidx]["annorect"]):
            # predictions and GT are present
            # iterate over GT poses
            for ridxGT in range(len(gtFrames[imgidx]["annorect"])):
                # GT pose
                rectGT = gtFrames[imgidx]["annorect"][ridxGT]
                # compute reference distance as head size
                headSize = getHeadSize(rectGT["x1"][0], rectGT["y1"][0],
                                                    rectGT["x2"][0], rectGT["y2"][0])
                pointsGT = []
                if len(rectGT["annopoints"]) > 0:
                    pointsGT = rectGT["annopoints"][0]["point"]
                # iterate over predicted poses
                for ridxPr in range(len(prFrames[imgidx]["annorect"])):
                    # predicted pose
                    rectPr = prFrames[imgidx]["annorect"][ridxPr]
                    pointsPr = rectPr["annopoints"][0]["point"]

                    # iterate over all possible body joints
                    for i in range(nJoints):
                        # GT joint
                        ppGT = getPointGTbyID(pointsGT, i)
                        # predicted joint
                        ppPr = getPointGTbyID(pointsPr, i)
                        # compute distance between predicted and GT joint locations
                        if hasPr[ridxPr, i] and hasGT[ridxGT, i]:
                            pointGT = [ppGT["x"][0], ppGT["y"][0]]
                            pointPr = [ppPr["x"][0], ppPr["y"][0]]
                            dist[ridxPr, ridxGT, i] = np.linalg.norm(np.subtract(pointGT, pointPr)) / headSize

            dist = np.array(dist)
            hasGT = np.array(hasGT)

            # number of annotated joints
            nGTp = np.sum(hasGT, axis=1)
            match = dist <= distThresh
            pck = 1.0 * np.sum(match, axis=2)
            for i in range(hasPr.shape[0]):
                for j in range(hasGT.shape[0]):
                    if nGTp[j] > 0:
                        pck[i, j] = pck[i, j] / nGTp[j]

            # preserve best GT match only
            idx = np.argmax(pck, axis=1)
            val = np.max(pck, axis=1)
            for ridxPr in range(pck.shape[0]):
                for ridxGT in range(pck.shape[1]):
                    if (ridxGT != idx[ridxPr]):
                        pck[ridxPr, ridxGT] = 0
            prToGT = np.argmax(pck, axis=0)
            val = np.max(pck, axis=0)
            prToGT[val == 0] = -1

            # info to compute MOT metrics
            mot = {}
            for i in range(nJoints):
                mot[i] = {}

            for i in range(nJoints):
                ridxsGT = np.argwhere(hasGT[:,i] == True); ridxsGT = ridxsGT.flatten().tolist()
                ridxsPr = np.argwhere(hasPr[:,i] == True); ridxsPr = ridxsPr.flatten().tolist()
                mot[i]["trackidxGT"] = [trackidxGT[idx] for idx in ridxsGT]
                mot[i]["trackidxPr"] = [trackidxPr[idx] for idx in ridxsPr]
                mot[i]["ridxsGT"] = np.array(ridxsGT)
                mot[i]["ridxsPr"] = np.array(ridxsPr)
                mot[i]["dist"] = np.full((len(ridxsGT),len(ridxsPr)),np.nan)
                for iPr in range(len(ridxsPr)):
                    for iGT in range(len(ridxsGT)):
                        if (match[ridxsPr[iPr], ridxsGT[iGT], i]):
                            mot[i]["dist"][iGT,iPr] = dist[ridxsPr[iPr], ridxsGT[iGT], i]

            # assign predicted poses to GT poses
            for ridxPr in range(hasPr.shape[0]):
                if (ridxPr in prToGT):  # pose matches to GT
                    # GT pose that matches the predicted pose
                    ridxGT = np.argwhere(prToGT == ridxPr)
                    assert(ridxGT.size == 1)
                    ridxGT = ridxGT[0,0]
                    s = score[ridxPr, :]
                    m = np.squeeze(match[ridxPr, ridxGT, :])
                    hp = hasPr[ridxPr, :]
                    for i in range(len(hp)):
                        if (hp[i]):
                            scoresAll[i][imgidx] = np.append(scoresAll[i][imgidx], s[i])
                            labelsAll[i][imgidx] = np.append(labelsAll[i][imgidx], m[i])

                else:  # no matching to GT
                    s = score[ridxPr, :]
                    m = np.zeros([match.shape[2], 1], dtype=bool)
                    hp = hasPr[ridxPr, :]
                    for i in range(len(hp)):
                        if (hp[i]):
                            scoresAll[i][imgidx] = np.append(scoresAll[i][imgidx], s[i])
                            labelsAll[i][imgidx] = np.append(labelsAll[i][imgidx], m[i])
        else:
            if not len(gtFrames[imgidx]["annorect"]):
                # No GT available. All predictions are false positives
                for ridxPr in range(hasPr.shape[0]):
                    s = score[ridxPr, :]
                    m = np.zeros([nJoints, 1], dtype=bool)
                    hp = hasPr[ridxPr, :]
                    for i in range(len(hp)):
                        if hp[i]:
                            scoresAll[i][imgidx] = np.append(scoresAll[i][imgidx], s[i])
                            labelsAll[i][imgidx] = np.append(labelsAll[i][imgidx], m[i])

        # save number of GT joints
        for ridxGT in range(hasGT.shape[0]):
            hg = hasGT[ridxGT, :]
            for i in range(len(hg)):
                nGTall[i, imgidx] += hg[i]

        motAll[imgidx] = mot

    return scoresAll, labelsAll, nGTall, motAll
