#!/bin/bash

TAG=${GITHUB_REF#refs/tags/}

if [ ${TAG} == ${GITHUB_REF} ];
then
    echo 'Invalid tag name'
    exit 1
fi

REPO=${GITHUB_SERVER_URL}/${GITHUB_REPOSITORY}

RELEASE=$(gh release view ${TAG} -R ${REPO} 2>&1)

PLETHYSMO_DMG=plethysmo-${TAG}-macOS-amd64.dmg

if [ "${RELEASE}"=="release not found" ];
then
    gh release create ${TAG} --notes-file CHANGELOG.md --title ${TAG} -R ${REPO}
fi

gh release upload ${TAG} ${PLETHYSMO_DMG} -R ${REPO}

